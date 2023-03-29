import os
import json
import boto3
from botocore.config import Config

my_config = Config(
    region_name = 'us-east-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

# # SSO LOGIN
# # get token from filesystem file
# # list accounts with boto3 (output json?)
# # transform output to use with fzf
# # execute fzf program as floating window
# # copy output url on selection
# # open browser on selection
client = boto3.client('sso')

def main():
    accounts()

def accounts():
    # get token cached file
    tpath = "/home/wim/.aws/sso/cache/"
    tfile = os.listdir(tpath)[1]

    # get token value
    with open(tpath + tfile, 'r') as f:
        data = json.load(f)
        token = data['accessToken']
        # print(token)

    # list accounts
    accounts = client.list_accounts(accessToken=token, maxResults=100)
    # o = json.dumps(accounts, indent=2)

    # '|' separated table with role, accountId, accountName, emailAddress
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

    os.system("cat cache | column -t -s, | fzf --header-lines=1")
