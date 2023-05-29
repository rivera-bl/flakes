import boto3
import os
import sys
import csv
import subprocess
import argparse

def get_account_id():
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        account_id = response['Account']
        return account_id
    except Exception as e:
        print(f"Error retrieving account ID: {e}")
        sys.exit()

account = get_account_id()
# account = "817860761669" # faster testing
region = "us-east-1"
cache_path = "/tmp/fim"
csvfile = f"{cache_path}/{account}_images.csv"
container = "sudo podman"
registry = f"{account}.dkr.ecr.{region}.amazonaws.com"
session = boto3.Session(region_name=region)

command_ecr = f"cat {csvfile} \
        | sed 's/^[^/]*\///' \
        | column -t -s, \
        | fzf --header-lines=1 \
            --header \"| enter:exec | ctrl-p:pull | ctrl-y:yank | ctrl-space:preview (policy) |\" \
            --prompt=\"{account}>\" \
            --height=100% \
            --multi \
            --preview-window right,hidden,40% \
            --preview \"set -o pipefail \
                       && cut -d':' -f1 <<< {{1}} \
                       | xargs -I {{}} aws ecr get-repository-policy --repository-name {{}} --query 'policyText' --output text \
                       | sed -e 's/\\\\\n//g' -e 's/\\\\\//g' | jq -r . \
                       | bat -l json\" \
            --bind \"ctrl-h:execute-silent(tmux select-pane -L)\" \
              --bind 'ctrl-p:execute-multi({container} pull {registry}/{{1}})' \
              --bind 'ctrl-y:execute-silent(echo {registry}/{{1}} \
                                    | clip.exe \
                                    && echo \"Copied {registry}/{{1}} to clipboard\")' \
              --bind 'enter:execute({container} run -ti --rm --entrypoint=bash {registry}/{{1}} \
                                    || {container} run -ti --rm --entrypoint=sh {registry}/{{1}})+abort' \
              --bind 'ctrl-space:toggle-preview'"

# """ fixes escaping nightmare
command_local = f"""{container} images --format '{{{{.Repository}}}}:{{{{.Tag}}}} {{{{.Size}}}} {{{{.ID}}}}' \
            | column -t \
            | fzf \
              --header "| enter:exec | ctrl-d:rmi | ctrl-p:push | ctrl-v:inspect | ctrl-space:preview |" \
              --prompt="local>" \
              --height=100% \
              --multi \
              --preview-window right,hidden,60% \
              --preview "{container} inspect {{4}} | bat -l json --color always" \
                  --bind "ctrl-h:execute-silent(tmux select-pane -L)" \
                  --bind "ctrl-v:execute({container} inspect {{4}} | nvim -R -c 'set syntax=json')" \
                  --bind "ctrl-d:execute-multi({container} rmi {{4}} --force)+reload-sync({container} images --format '{{{{.Repository}}}}:{{{{.Tag}}}} {{{{.Size}}}} {{{{.ID}}}}' | column -t)" \
                  --bind 'ctrl-p:execute-multi({container} push {{1}})' \
                  --bind "enter:execute({container} run -ti --rm --entrypoint=bash {{1}} || {container} run -ti --rm --entrypoint=sh {{1}})" \
                  --bind 'ctrl-space:toggle-preview'"""

# write as csv a list of lists
def write_csv(csvfile, data):
    # delete csv if already exists
    if os.path.exists(csvfile):
        os.remove(csvfile)

    # save as csv
    os.makedirs(os.path.dirname(csvfile), exist_ok=True)
    with open(csvfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    print(f"Images written to {csvfile}.")

# print as columns a list of lists
def print_columns(data):
    widths = [max(map(len, col)) for col in zip(*data)]
    for row in data:
        print("  ".join((val.ljust(width) for val, width in zip(row, widths))))

# human readable bytes
def sizeof_fmt(num, suffix='B'):
    # Adapted from https://stackoverflow.com/a/1094933/6465438
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "{:.1f}{}{}".format(num, unit, suffix)
        num /= 1024.0
    return "{:.1f}{}{}".format(num, 'Yi', suffix)

# list ecr_images as a list of list
def list_ecr_images():
    images = []
    ecr_client = session.client('ecr')

    print(f"Retrieving repositories for {registry}...")
    response = ecr_client.describe_repositories()
    print("Repositories retrieved.")

    for repository in response['repositories']:
        repository_name = repository['repositoryName']

        image_response = ecr_client.describe_images(repositoryName=repository_name)
        print(f"Images retrieved for repository: {repository_name}.")

        for image in image_response['imageDetails']:
            if 'imageTags' not in image:
                continue
            image_tags = image['imageTags']
            for tag in image_tags:
                image_tag = f"{registry}/{repository_name}:{tag}"

                image_pushed_date = image['imagePushedAt'].strftime("%Y-%m-%d %H:%M:%S")
                image_size = image['imageSizeInBytes']

                images.append([image_tag, image_pushed_date, sizeof_fmt(image_size)])

    print("Sorting images by PushedDate ...")
    sorted_images = sorted(images[1:], key=lambda x: x[1], reverse=True)
    sorted_images.insert(0, ["Image", "Pushed", "Size"])
    print("Images sorted.")

    # print_columns(sorted_images)
    return sorted_images

def main():
    parser = argparse.ArgumentParser(description='Container Registry actions with fzf')
    parser.add_argument('--load', action='store_true', help=f'Load ECR images into {cache_path}/{{account}}_images.csv')
    parser.add_argument('--local', action='store_true', help=f'Open LOCAL registry with fzf')
    parser.add_argument('--ecr', action='store_true', help=f'Open ECR registry with fzf')
    args = parser.parse_args()

    if not any(args.__dict__.values()):
        parser.print_help()
        exit()

    if not os.path.exists(csvfile) or args.load:
        images = list_ecr_images()
        write_csv(csvfile, images)
        subprocess.run(command_ecr, shell=True)
    elif args.local:
        subprocess.run(command_local, shell=True)
    elif args.ecr:
        subprocess.run(command_ecr, shell=True)
