# # SSO LOGIN
# # get token from filesystem file
# # list accounts with boto3
# # transform output to use with fzf
# # execute fzf program as floating window
# # TODO copy output url on selection
# # TODO open browser on selection
# # TODO create function to fill ~/.aws/config file with the sessions definition, use ROLE_ACCOUNT as session name
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
my_config = Config(
    region_name = 'us-east-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

def main():
    load()
    # sso_session = menu()
    # login(sso_session)

def menu():
    # piped cat and fzf
    commas  = subprocess.Popen(['cat', 'cache'], stdout=subprocess.PIPE)
    columns = subprocess.Popen(['column', '-t', '-s,'], stdin=commas.stdout, stdout=subprocess.PIPE)
    fzf     = subprocess.Popen(['fzf', '--header-lines=1'], stdin=columns.stdout, stdout=subprocess.PIPE)

    # fzf menu and save selection
    selraw = fzf.stdout.read()
    
    # match the string that is on the beggining and before the first space
    accountId = re.search(r'^\S+', selraw.decode('utf-8'))
    # string that matchs the second column
    roleName = re.search(r'(?<=\s)\S+', selraw.decode('utf-8'))

    # TODO return selraw as array
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
    for account in accounts['accountList']:
        # list roles for account using accountId
        roles = client.list_account_roles(accessToken=token, accountId=account['accountId'])

        # print roleName, accountId, accountName, emailAddress for each accountId
        for role in roles['roleList']:
            o = account['accountId'], role['roleName'], account['accountName'], account['emailAddress']
            s += ','.join(o) + "\n"
            # join accountId and roleName as sso_session
            sso_session = account['accountId'] + '_' + role['roleName']

            # TODO how to append new keys to a dictionary
            t = {
                'profile ' + sso_session: {
                    'sso_session': sso_session,
                    'sso_account_id': account['accountId'],
                    'sso_role_name': role['roleName'],
                    'region': 'us-east-1',
                    'output': 'json'
                },
                'sso-session ' + sso_session: {
                    'sso_start_url': 'https://d-90675d22db.awsapps.com/start#',
                    'sso_region': 'us-east-1',
                    'sso_registration_scopes': 'sso:account:access'
                }
            }

    print(t)
    # save s to file on disk on current directory
    with open('cache', 'w') as f:
        f.write(s)

    with open('datos.toml', 'w') as archivo:
            toml.dump(t, archivo)

    # # TODO generate ~/.aws/config file
    # # TODO remove ""
    # # split sso_session separated by _
    # session_values = sso_session.split('_')

    # t = {
		# 'profile ' + sso_session: {
    #         'sso_session': sso_session,
    #         'sso_account_id': session_values[0],
    #         'sso_role_name': session_values[1],
    #         'region': 'us-east-1',
    #         'output': 'json'
		# },
    #     'sso-session ' + sso_session: {
    #         'sso_start_url': 'https://d-90675d22db.awsapps.com/start#',
    #         'sso_region': 'us-east-1',
    #         'sso_registration_scopes': 'sso:account:access'
    #     }
	# }

	# # Escribir el diccionario en un archivo TOML
    # with open('datos.toml', 'w') as archivo:
    #     toml.dump(t, archivo)
    # # TODO generate ~/.aws/config file
