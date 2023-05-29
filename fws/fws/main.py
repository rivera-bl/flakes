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
    # login
    if subprocess.call("which tmux >/dev/null 2>&1", shell=True) == 0:
        tmux_session_setenv("AWS_PROFILE", sso_session)
    loggedin = subprocess.run(
        ['aws', 'sts', 'get-caller-identity', '--profile', sso_session], capture_output=True)
    # TODO fix this! sometimes false positive
    # if loggedin.returncode == 0:
    #     print("\nYou are already authenticated with " + sso_session + "!")
    #     time.sleep(1)
    #     exit()

    os.system('aws sso login --no-browser --profile ' + sso_session)
    print('\nUse this profile with `export AWS_PROFILE=' + sso_session + '`')


def tmux_session_setenv(envar, sso_session):
    if shutil.which('tmux') is not None:
        # setenv
        os.system('tmux setenv AWS_PROFILE ' + sso_session)
        # export all zsh panes
        command = "tmux list-panes -s -F '#{pane_id} #{pane_current_command}' | grep 'zsh' | cut -d' ' -f1 \
                | xargs -I {} tmux send-keys -t {} \
                'export " + envar + "=" + sso_session + "' Enter C-l"
        os.system(command)
    else:
        os.system("export " + envar + "=" + sso_session)


def sessions():
    output = subprocess.check_output(
        "grep sso-session ~/.aws/config | awk '{print $2}' | sed -s 's/[]]//g'", shell=True)
    sessions = output.decode().strip()
    return sessions


def accounts():
    # get latest sso token cached file
    tpath = "/home/wim/.aws/sso/cache/"
    tfiles = [os.path.join(tpath, x) for x in os.listdir(tpath)]
    tnewest = max(tfiles, key=os.path.getctime)

    # get token value
    with open(tnewest, 'r') as f:
        data = json.load(f)
        token = data['accessToken']

    # list accounts
    accountsraw = client.list_accounts(accessToken=token, maxResults=100)

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
