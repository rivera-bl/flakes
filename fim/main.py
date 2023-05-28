import boto3
import os
import csv
import subprocess
import argparse

# TODO convert into a command line tool with help and args
# # merge with localhost function
# TODO fix ecr-credential-helper
# # for this we have to pull the image first
# TODO add to fzf menu
# TODO --bind inspect image (ctrl-v)
# TODO --bind open repository in browser (ctr-o)

def get_account_id():
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        account_id = response['Account']
        return account_id
    except Exception as e:
        print(f"Error retrieving account ID: {e}")
        return None

account = get_account_id()
region = "us-east-1"
cache_path = "/tmp/fim"
csvfile = f"{cache_path}/{account}_images.csv"
container = "sudo podman"
registry = f"{account}.dkr.ecr.{region}.amazonaws.com"
session = boto3.Session(region_name=region) # uses current AWS_PROFILE

# better way to pass commands? escaping is a pain
command = f"cat {csvfile} \
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
                       | xargs -I {{}} aws ecr get-repository-policy --repository-name {{}} --query 'policyText' --output text | sed -e 's/\\\\\n//g' -e 's/\\\\\//g' | jq -r . \
                       | bat -l json\" \
            --bind \"ctrl-h:execute-silent(tmux select-pane -L)\" \
              --bind 'ctrl-p:execute-multi({container} pull {registry}/{{1}})' \
              --bind 'ctrl-y:execute-silent(echo {registry}/{{1}} \
                                    | clip.exe \
                                    && echo \"Copied {registry}/{{1}} to clipboard\")' \
              --bind 'enter:execute({container} run -ti --rm --entrypoint=bash {registry}/{{1}} \
                                    || {container} run -ti --rm --entrypoint=sh {registry}/{{1}})+abort' \
              --bind 'ctrl-space:toggle-preview'"

# human readable bytes
def sizeof_fmt(num, suffix='B'):
    # Adapted from https://stackoverflow.com/a/1094933/6465438
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "{:.1f}{}{}".format(num, unit, suffix)
        num /= 1024.0
    return "{:.1f}{}{}".format(num, 'Yi', suffix)

# TODO print information of the actions it is doing
def list_ecr_images():
    images = []
    ecr_client = session.client('ecr')

    response = ecr_client.describe_repositories()

    for repository in response['repositories']:
        repository_name = repository['repositoryName']

        image_response = ecr_client.describe_images(repositoryName=repository_name)

        for image in image_response['imageDetails']:
            if 'imageTags' not in image:
                continue
            image_tags = image['imageTags']
            for tag in image_tags:
                registry = image['registryId'] + "dkr.ecr." + region + ".amazonaws.com/"
                image_tag = registry + repository_name + ":" + tag

                image_pushed_date = image['imagePushedAt'].strftime("%Y-%m-%d %H:%M:%S")
                image_size = image['imageSizeInBytes']

                images.append([image_tag, image_pushed_date, sizeof_fmt(image_size)])

    # # By saving as list of list, we can either save to csv, or output as columns from py
    # Sort in descending order by Pushed date
    sorted_images = sorted(images[1:], key=lambda x: x[1], reverse=True)
    sorted_images.insert(0, ["Image", "Pushed", "Size"])

    # TODO move to another function with csv
    # delete csv if already exists
    if os.path.exists(csvfile):
        os.remove(csvfile)

    # save as csv
    os.makedirs(cache_path, exist_ok=True)
    with open(csvfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(sorted_images)

    # # same as shell 'column -t'
    # # TODO move to another function
    # widths = [max(map(len, col)) for col in zip(*sorted_images)]
    # for row in sorted_images:
    #     print("  ".join((val.ljust(width) for val, width in zip(row, widths))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Container Registry actions with fzf')
    parser.add_argument('--load', action='store_true', help=f'Load ECR images into {cache_path}/{{account}}_images.csv')
    args = parser.parse_args()

    if not any(args.__dict__.values()):
        parser.print_help()
        exit()

    if not os.path.exists(csvfile) or args.load:
        list_ecr_images()
    subprocess.run(command, shell=True)
