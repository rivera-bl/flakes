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
def main():
    for account in account_list():
        print(account['accountId'], "|",
              account['accountName'], "|",
              account['emailAddress'])

def account_list():
    # get token cached file
    tpath = "/home/wim/.aws/sso/cache/"
    tfile = os.listdir(tpath)[1]

    # get token value
    with open(tpath + tfile, 'r') as f:
        data = json.load(f)
        token = data['accessToken']
        # print (token)

    # list accounts
    client = boto3.client('sso')
    accounts = client.list_accounts(accessToken=token)
    # o = json.dumps(accounts, indent=2)
    # print(o)

    return accounts['accountList']
