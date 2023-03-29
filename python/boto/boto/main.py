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

# TODO format output with role names
# TODO save output to cache file
# TODO show with fzf tmux
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
    accounts = client.list_accounts(accessToken=token)
    o = json.dumps(accounts, indent=2)
    print(o)

    # for account in accounts:
        # roles = client.list_account_roles(accessToken=token, accountId=account['accountId'])
        # print(accountList)
        # for role in roles:
        #     print(account['accountId'], "|",
        #           account['accountName'], "|",
        #           account['emailAddress'], "|",
        #           role['roleName'])

    # return accounts['accountList']
