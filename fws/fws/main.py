# # SSO LOGIN
# # get token from filesystem file
# # list accounts with boto3
# # transform output to use with fzf
# # aws sso login
# # set AWS_PROFILE with tmux

import os
import time
import re
import shutil
import json
import argparse
import boto3
import toml
import subprocess
from botocore.config import Config

my_config = Config(
    region_name='us-east-1',
    signature_version='v4',
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)
client = boto3.client('sso', config=my_config)
home = os.path.expanduser("~/")
cache_path = '/tmp/fws/accounts.csv'

# set flags
parser = argparse.ArgumentParser(description='AWS SSO Login with fzf')
parser.add_argument('--load', type=str, metavar='sso_start_url', help='Load accounts in `' +
                    cache_path + '` and sso.sessions in `~/.aws/config`, takes `sso_start_url` as an argument')
parser.add_argument('--login', action='store_true',  help='Pipe `' +
                    cache_path + '` into FZF to select account to login with AWS SSO')
parser.add_argument('--send-all', action='store_true', help='In tmux: Set session AWS_PROFILE and send export command to ALL panes.')
parser.add_argument('--send-here', action='store_true', help='In tmux: Set session AWS_PROFILE and send export command to CURRENT pane.')


args = parser.parse_args()

# show help if no flag
if not any(args.__dict__.values()):
    parser.print_help()
    exit()


def main():
    if args.load:
        acc, config = accounts()
        load(acc, config)
    elif args.login:
        login(menu("login> "))


def login(sso_session):
    # Check if already logged in (optional, kept original logic)
    loggedin = subprocess.run(
        ['aws', 'sts', 'get-caller-identity', '--profile', sso_session], capture_output=True)
    # TODO fix this! sometimes false positive
    # if loggedin.returncode == 0:
    #     print("\nYou are already authenticated with " + sso_session + "!")
    #     time.sleep(1)
    #     exit()

    # Attempt SSO login
    print(f"Attempting AWS SSO login for profile: {sso_session}...")
    login_command = ['aws', 'sso', 'login', '--profile', sso_session]
    # Use subprocess.run to capture status, but let user interact with stdin/stdout/stderr
    result = subprocess.run(login_command)

    # Check if login was successful
    if result.returncode == 0:
        print(f"\nSuccessfully logged in with profile: {sso_session}")
        # Check if running inside tmux
        if shutil.which('tmux') is not None:
            did_tmux_action = False
            # Set session env if either flag is present
            if args.send_all or args.send_here:
                tmux_set_session_env("AWS_PROFILE", sso_session)
                print("Set AWS_PROFILE for tmux session.")
                did_tmux_action = True # Mark that we set the session env

            # Send keys based on flags
            if args.send_all:
                print("Sending AWS_PROFILE export to all zsh panes...")
                tmux_send_keys_all_panes("AWS_PROFILE", sso_session)
                print("Export command sent to all zsh panes.")
                did_tmux_action = True # Mark that we sent keys
            elif args.send_here: # Use elif to avoid sending twice if both flags are somehow set
                print("Sending AWS_PROFILE export to current pane...")
                tmux_send_keys_current_pane("AWS_PROFILE", sso_session)
                print("Export command sent to current pane.")
                did_tmux_action = True # Mark that we sent keys

            if not did_tmux_action:
                 print("Login successful. AWS_PROFILE not automatically exported to panes (use --send-all or --send-here).")

        else:
            # Outside tmux: print the export command for the user
            print(f'\nLogin successful. Use this profile in your shell:')
            print(f'export AWS_PROFILE={sso_session}')
            print(f'\n# Run this command to apply:', file=os.sys.stderr)
            print(f'# eval "$(fws --login)"', file=os.sys.stderr)

    else:
        print(f"\nAWS SSO login failed for profile: {sso_session}", file=os.sys.stderr)


def tmux_set_session_env(envar, value):
    """Sets a tmux session environment variable."""
    if shutil.which('tmux') is not None:
        os.system(f'tmux setenv {envar} {value}')

def tmux_send_keys_all_panes(envar, value):
    """Sends export command to all zsh panes in the current tmux session."""
    if shutil.which('tmux') is not None:
        # export all zsh panes
        command = f"tmux list-panes -s -F '#{{pane_id}} #{{pane_current_command}}' | grep 'zsh' | cut -d' ' -f1 \
                | xargs -I {{}} tmux send-keys -t {{}} \
                'export {envar}={value}' Enter C-l"
        os.system(command)

def tmux_send_keys_current_pane(envar, value):
    """Sends export command to the current tmux pane."""
    if shutil.which('tmux') is not None:
        command = f"tmux send-keys 'export {envar}={value}' Enter C-l"
        os.system(command)


def sessions():
    output = subprocess.check_output(
        "grep sso-session ~/.aws/config | awk '{print $2}' | sed -s 's/[]]//g'", shell=True)
    sessions = output.decode().strip()
    return sessions


def accounts():
    # get latest sso token cached file
    tpath = home + ".aws/sso/cache/"
    tfiles = [os.path.join(tpath, x) for x in os.listdir(tpath)]
    tnewest = max(tfiles, key=os.path.getctime)

    # get token value
    with open(tnewest, 'r') as f:
        data = json.load(f)
        token = data['accessToken']

    # list accounts
    accountsraw = client.list_accounts(accessToken=token, maxResults=1000)

    # format to ',' separated strings
    accounts = "accountId,roleName,accountName,emailAddress\n"
    config = {}
    for account in accountsraw['accountList']:
        # list roles for account using accountId
        roles = client.list_account_roles(
            accessToken=token, accountId=account['accountId'])

        # list of roleName, accountId, accountName, emailAddress for each accountId
        for role in roles['roleList']:
            o = account['accountId'], role['roleName'], account['accountName'], account['emailAddress']
            accounts += ','.join(o) + "\n"

            # join accountId and roleName as sso_session
            sso_session = account['accountId'] + '_' + role['roleName']

            # create dictionary to save to toml file
            config['profile ' + sso_session] = {
                'sso_session': sso_session,
                'sso_account_id': account['accountId'],
                'sso_role_name': role['roleName'],
                'region': 'us-east-1',
                'output': 'json'
            }
            config['sso-session ' + sso_session] = {
                'sso_start_url': parser.parse_args().load,
                'sso_region': 'us-east-1',
                'sso_registration_scopes': 'sso:account:access'
            }

    return accounts, config


def load(accounts, config):
    # save accounts to $cache_path
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w') as f:
        f.write(accounts)

    # save sessions to ~/.aws/config
    with open(home + '.aws/config', 'w') as f:
        toml.dump(config, f)

    # remove quotes from file ~/.aws/config
    with open(home + '.aws/config', 'r') as f:
        tq = f.read()

    tr = tq.replace('"', '')

    with open(home + '.aws/config', 'w') as f:
        f.write(tr)


def menu(prompt):
    if not os.path.isfile(cache_path):
        print('No accounts found. Please run `fws --load ${sso_start_url}`')
        exit()
    # piped cat and fzf
    commas = subprocess.Popen(['cat', cache_path], stdout=subprocess.PIPE)
    columns = subprocess.Popen(
        ['column', '-t', '-s,'], stdin=commas.stdout, stdout=subprocess.PIPE)
    fzf = subprocess.Popen(['fzf', '--prompt=' + prompt, '--min-height=20',
                           '--header-lines=1'], stdin=columns.stdout, stdout=subprocess.PIPE)

    # fzf menu and save selection
    selraw = fzf.stdout.read()
    if not selraw:
        exit()

    # match the string that is on the beggining and before the first space
    accountId = re.search(r'^\S+', selraw.decode('utf-8'))
    # string that matchs the second column
    roleName = re.search(r'(?<=\s)\S+', selraw.decode('utf-8'))

    sso_session = accountId.group(0) + "_" + roleName.group(0)
    return sso_session
