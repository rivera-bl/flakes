# # SSO LOGIN
# # get token from filesystem file
# # list accounts with boto3
# # transform output to use with fzf
# # execute fzf program as floating window
# # TODO handle error when not picking an account to login
# # TODO save cache to tmp directory
# # TODO set AWS_PROFILE with tmux env and set starship
# # TODO get url from output
# # TODO open browser
# # TODO turn into a binary 'fws' with different functions for login, load sessions, load accounts
# # TODO document --help

import os
import re
import json
import boto3
import toml
import subprocess
from botocore.config import Config

client    = boto3.client('sso')
home      = os.path.expanduser("~/")
my_config = Config(
    region_name = 'us-east-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

def main():
    # load()
    sso_session = menu()
    login(sso_session)

def menu():
    # piped cat and fzf
    commas  = subprocess.Popen(['cat', home + 'code/personal/flakes/python/fws/cache'], stdout=subprocess.PIPE)
    columns = subprocess.Popen(['column', '-t', '-s,'], stdin=commas.stdout, stdout=subprocess.PIPE)
    fzf     = subprocess.Popen(['fzf', '--min-height=20', '--header-lines=1'], stdin=columns.stdout, stdout=subprocess.PIPE)

    # fzf menu and save selection
    selraw = fzf.stdout.read()

    # match the string that is on the beggining and before the first space
    accountId = re.search(r'^\S+', selraw.decode('utf-8'))
    # string that matchs the second column
    roleName = re.search(r'(?<=\s)\S+', selraw.decode('utf-8'))

    sso_session = accountId.group(0) + "_" + roleName.group(0) 
    return sso_session

def login(sso_session):
    os.system('aws sso login --no-browser --profile ' + sso_session)

def load():
    # get token cached file
    tpath = "/home/wim/.aws/sso/cache/"
    tfiles = [os.path.join(tpath, x) for x in os.listdir(tpath)]
    tnewest = max(tfiles , key = os.path.getctime)

    # get token value
    with open(tnewest, 'r') as f:
        data = json.load(f)
        token = data['accessToken']

    # list accounts
    accounts = client.list_accounts(accessToken=token, maxResults=100)

    # format to ',' separated strings
    s = "accountId,roleName,accountName,emailAddress\n"
    t = {}
    for account in accounts['accountList']:
        # list roles for account using accountId
        roles = client.list_account_roles(accessToken=token, accountId=account['accountId'])

        # list of roleName, accountId, accountName, emailAddress for each accountId
        for role in roles['roleList']:
            o = account['accountId'], role['roleName'], account['accountName'], account['emailAddress']
            s += ','.join(o) + "\n"

            # join accountId and roleName as sso_session
            sso_session = account['accountId'] + '_' + role['roleName']

            # create dictionary to save to toml file
            t['profile ' + sso_session] = {
                'sso_session': sso_session,
                'sso_account_id': account['accountId'],
                'sso_role_name': role['roleName'],
                'region': 'us-east-1',
                'output': 'json' 
            }
            t['sso-session ' + sso_session] = {
                'sso_start_url': 'https://d-90675d22db.awsapps.com/start#',
                'sso_region': 'us-east-1',
                'sso_registration_scopes': 'sso:account:access'
            }

    # save accounts to file on disk on current directory
    with open('cache', 'w') as f:
        f.write(s)

    # save sessions to ~/.aws/config
    with open(home + '.aws/config', 'w') as f:
        toml.dump(t, f)

    # remove quotes from file ~/.aws/config
    with open(home + '.aws/config', 'r') as f:
        tq = f.read()

    tr = tq.replace('"', '')

    with open(home + '.aws/config', 'w') as f:
        f.write(tr)
