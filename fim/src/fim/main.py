import boto3
import os
import sys
import csv
import subprocess
import argparse
import requests

# TODO only run get_account_id for --ecr
# TODO run command should go with tmux send-keys for passing arguments
def get_account_id():
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        account_id = response['Account']
        return account_id
    except Exception as e:
        print(f"Error retrieving account ID: {e}")
        sys.exit()

region = "us-east-1"
cache_path = "/tmp/fim"
account = get_account_id()
csvfile = f"{cache_path}/{account}_images.csv"
registry = f"{account}.dkr.ecr.{region}.amazonaws.com"
container = "sudo podman"
session = boto3.Session(region_name=region)

# # shows policy
# --preview \"set -o pipefail \
#            && cut -d':' -f1 <<< {{1}} \
#            | xargs -I {{}} aws ecr get-repository-policy --repository-name {{}} --query 'policyText' --output text \
#            | sed -e 's/\\\\\n//g' -e 's/\\\\\//g' | jq -r . \
#            | bat -l json\" \
command_ecr = f"cat {csvfile} \
        | sed 's/^[^/]*\///' \
        | column -t -s, \
        | fzf --header-lines=1 \
            --header \"| enter:run | ctrl-x:exec | ctrl-p:pull | ctrl-y:yank | ctrl-v:inspect | ctrl-space:preview |\" \
            --prompt=\"{account}>\" \
            --height=100% \
            --multi \
            --preview-window right,hidden,60% \
            --preview 'crane config {registry}/{{1}} | jq . | bat -l json --color always' \
              --bind \"ctrl-h:execute-silent(tmux select-pane -L)\" \
              --bind 'ctrl-p:execute-multi({container} pull {registry}/{{1}})' \
              --bind \"ctrl-v:execute(crane config {registry}/{{1}} | jq . | nvim -R -c 'set syntax=json')\" \
              --bind 'ctrl-y:execute-silent(echo {registry}/{{1}} \
                                    | clip.exe \
                                    && echo \"Copied {registry}/{{1}} to clipboard\")' \
              --bind 'enter:execute({container} run {{1}})'+abort \
              --bind 'ctrl-x:execute({container} run -ti --rm --entrypoint=bash {registry}/{{1}} \
                                    || {container} run -ti --rm --entrypoint=sh {registry}/{{1}})+abort' \
              --bind 'ctrl-space:toggle-preview'"

command_local = f"""{container} images --format '{{{{.Repository}}}}:{{{{.Tag}}}} {{{{.Size}}}} {{{{.ID}}}}' \
            | column -t \
            | fzf \
              --header "| enter:run | ctr-x:exec | ctrl-d:rmi | ctrl-p:push | ctrl-v:inspect | ctrl-space:preview |" \
              --prompt="local>" \
              --height=100% \
              --multi \
              --preview-window right,hidden,60% \
              --preview "{container} inspect {{4}} | bat -l json --color always" \
                  --bind 'enter:execute({container} run {{1}})'+abort \
                  --bind "ctrl-h:execute-silent(tmux select-pane -L)" \
                  --bind "ctrl-v:execute({container} inspect {{4}} | nvim -R -c 'set syntax=json')" \
                  --bind "ctrl-d:execute-multi({container} rmi {{4}} --force)+reload-sync({container} images --format '{{{{.Repository}}}}:{{{{.Tag}}}} {{{{.Size}}}} {{{{.ID}}}}' | column -t)" \
                  --bind 'ctrl-p:execute-multi({container} push {{1}})' \
                  --bind "ctrl-x:execute({container} run -ti --rm --entrypoint=bash {{1}} || {container} run -ti --rm --entrypoint=sh {{1}})" \
                  --bind 'ctrl-space:toggle-preview'"""

def write_csv(csvfile, data):
    if os.path.exists(csvfile):
        os.remove(csvfile)

    os.makedirs(os.path.dirname(csvfile), exist_ok=True)
    with open(csvfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    print(f"Images written to {csvfile}.")

def print_columns(data):
    widths = [max(map(len, col)) for col in zip(*data)]
    for row in data:
        print("  ".join((val.ljust(width) for val, width in zip(row, widths))))

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "{:.1f}{}{}".format(num, unit, suffix)
        num /= 1024.0
    return "{:.1f}{}{}".format(num, 'Yi', suffix)

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

    return sorted_images


def fetch_dockerhub_tags(image_name):
    try:
        if '/' in image_name:
            url = f"https://hub.docker.com/v2/repositories/{image_name}/tags/?page_size=100"
        else:
            url = f"https://hub.docker.com/v2/repositories/library/{image_name}/tags/?page_size=100"
        response = requests.get(url)
        response.raise_for_status()
        tags_data = response.json()

        tags = []
        for tag_data in tags_data['results']:
            tag_name = f"{image_name}:{tag_data['name']}"
            last_pushed = tag_data['last_updated'].split('T')[0]
            size = tag_data['full_size']
            tags.append([tag_name, last_pushed, sizeof_fmt(size)])

        tags.insert(0, ["Image", "Last Pushed", "Size"])

        tag_options = "\n".join([",".join(tag) for tag in tags])

        return tag_options
    except Exception as e:
        print(f"Error fetching DockerHub tags: {e}")
        sys.exit()

def main():
    parser = argparse.ArgumentParser(description='Container Registry actions with fzf')
    parser.add_argument('--load', action='store_true', help=f'Load ECR images into `{cache_path}/{{account}}_images.csv`')
    parser.add_argument('--local', action='store_true', help=f'Fetch `local` registry with fzf')
    parser.add_argument('--ecr', action='store_true', help=f'Fetch `ecr` registry with fzf')
    parser.add_argument('--dockerhub', type=str, metavar='IMAGE_NAME', help='Fetch tags for a DockerHub image')
    args = parser.parse_args()

    if not any(args.__dict__.values()):
        parser.print_help()
        exit()

    if args.load:
        if os.path.exists(csvfile):
            print(f"Refreshing cache file {csvfile}.")
        images = list_ecr_images()
        write_csv(csvfile, images)
        subprocess.run(command_ecr, shell=True)
    elif args.local:
        subprocess.run(command_local, shell=True)
    elif args.ecr:
        if not os.path.exists(csvfile):
            print(f"Cache file {csvfile} not found.")
            images = list_ecr_images()
            write_csv(csvfile, images)
        subprocess.run(command_ecr, shell=True)
    elif args.dockerhub:
        image_name = args.dockerhub
        tags = fetch_dockerhub_tags(image_name)
        command_dockerhub = f"""echo '{tags}' \
            | column -t -s, \
            | fzf --header-lines=1 \
                --header '| enter:run | ctrl-p:pull | ctrl-x:exec | ctrl-v:inspect | ctrl-space:preview |' \
                --prompt='dockerhub>' \
                --height=60% \
                --multi \
                --preview-window right,hidden,60% \
                --preview "crane config {{1}} | jq . | bat -l json --color always" \
                    --bind "ctrl-h:execute-silent(tmux select-pane -L)" \
                    --bind 'ctrl-p:execute-multi({container} pull {{1}})' \
                    --bind 'ctrl-x:execute({container} run -ti --rm --entrypoint=bash {{1}} \
                                          || {container} run -ti --rm --entrypoint=sh {{1}})' \
                    --bind "ctrl-v:execute(crane config {{1}} | jq . | nvim -R -c 'set syntax=json')" \
                    --bind 'enter:execute({container} run {{1}})'+abort \
                    --bind 'ctrl-space:toggle-preview'""" 
        subprocess.run(command_dockerhub, shell=True)

if __name__ == "__main__":
    main()

