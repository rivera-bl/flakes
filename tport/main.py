import boto3
import os
import subprocess
from resource_schemas import resource_schemas

# TODO provider and version as arguments
# terraform import aws_lambda_function.backend LambdaRDSTest
# terraform state show aws_lambda_function.consul_backup_test > imports.tf

providers = '''terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.1.0"
    }
  }
  required_version = ">= 1.1.9"
}'''


def get_all_lambda_function_names():
    # Create a Boto3 Lambda client
    lambda_client = boto3.client('lambda')

    # Retrieve all Lambda function names
    response = lambda_client.list_functions()
    function_names = [function['FunctionName'] for function in response['Functions']]

    return function_names

schemas_join = "\n".join(resource_schemas)
menu_uno = f"""
    echo '{schemas_join}' | fzf
"""
output = subprocess.check_output(menu_uno, shell=True).decode().strip()

if output != "" and not os.path.exists('versions.tf'):
    with open('versions.tf', 'w') as file:
        file.write(providers)
    subprocess.run("terraform init", shell=True)
if output == 'aws_lambda_function':
    items = "\n".join(get_all_lambda_function_names())
else:
    exit()

# TODO multi not working with echo 
menu_dos = f"""
    echo '{items}' \
    | fzf \
        --bind "enter:execute(echo -e 'resource \\"{output}\\" \\"{{1}}\\" {{  }}' > resources.tf \
          && terraform import {output}.{{1}} {{1}} \
          && terraform state show -no-color {output}.{{1}} >> imports.tf)" \
        --bind "ctrl-h:execute-silent(tmux select-pane -L)" \
"""

subprocess.run(menu_dos, shell=True)
