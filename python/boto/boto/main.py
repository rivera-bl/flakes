# # SSO LOGIN
# # get token from filesystem file
# # list accounts with boto3
# # transform output to use with fzf
# # execute fzf program as floating window
# # TODO copy output url on selection
# # TODO open browser on selection

import os
import re
import json
import boto3
import subprocess
from botocore.config import Config

client    = boto3.client('sso')
my_config = Config(
    region_name = 'us-east-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

def main():
    # fetch_accounts()
    sso_session = menu()
    login(sso_session)

def fetch_accounts():
    # get token cached file
    tpath = "/home/wim/.aws/sso/cache/"
    tfile = os.listdir(tpath)[1]

    # get token value
    with open(tpath + tfile, 'r') as f:
        data = json.load(f)
        token = data['accessToken']

    # list accounts
    accounts = client.list_accounts(accessToken=token, maxResults=100)

    # format to ',' separated strings
    s = "accountId,roleName,accountName,emailAddress\n"
    for account in accounts['accountList']:
        # list roles for account using accountId
        roles = client.list_account_roles(accessToken=token, accountId=account['accountId'])

        # print roleName, accountId, accountName, emailAddress for each accountId
        for role in roles['roleList']:
            o = account['accountId'], role['roleName'], account['accountName'], account['emailAddress']
            s += ','.join(o) + "\n"

    # save s to file on disk on current directory
    with open('cache', 'w') as f:
        f.write(s)

def menu():
    # piped cat and fzf
    commas  = subprocess.Popen(['cat', 'cache'], stdout=subprocess.PIPE)
    columns = subprocess.Popen(['column', '-t', '-s,'], stdin=commas.stdout, stdout=subprocess.PIPE)
    fzf     = subprocess.Popen(['fzf', '--header-lines=1'], stdin=columns.stdout, stdout=subprocess.PIPE)

    # fzf menu and save selection
    sel = fzf.stdout.read()
    
    # match the string that is on the beggining and before the first space
    accountId = re.search(r'^\S+', sel.decode('utf-8'))
    # string that matchs the second column
    roleName = re.search(r'(?<=\s)\S+', sel.decode('utf-8'))

    sso_session = accountId.group(0) + "_" + roleName.group(0) 
    return sso_session

def login(sso_session):
    os.system('aws sso login --no-browser --profile ' + sso_session)
