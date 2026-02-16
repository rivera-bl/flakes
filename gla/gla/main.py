import os
import subprocess
import sys
import time
import gitlab
import csv
import argparse
import dotenv

# TODO change dir after cloning
# TODO describe repo preview and open with vi

GITLAB_SERVER = os.environ.get('GITLAB_SERVER', 'https://gitlab.com')
GITLAB_TOKEN = os.environ.get('GITLAB_TOKEN')
cache_path = '~/.gla/projects.csv'
open_bin = 'wsl-open'
basedir = os.path.expanduser('~/code/gitlab')

def get_projects():
    if not GITLAB_TOKEN:
        print("Please set the GITLAB_TOKEN env variable.")
        sys.exit(1)
    gl = gitlab.Gitlab(GITLAB_SERVER, GITLAB_TOKEN)

    max_retries = 5
    for attempt in range(max_retries):
        try:
            gl.auth()
            print(f"Retrieving projects from {GITLAB_SERVER}..")
            projects = gl.projects.list(all=True)
            break
        except gitlab.exceptions.GitlabError as e:
            if attempt < max_retries - 1 and getattr(e, 'response_code', None) in (502, 503, 504):
                wait = 2 ** attempt
                print(f"Got {e.response_code}, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
    project_list = []

    # Add the header to the project_list
    header = ['Id', 'Repository']
    project_list.append(header)

    for project in projects:
        project_info = [str(project.id), project.ssh_url_to_repo]
        project_list.append(project_info)
    return project_list

def get_ssh_and_web_hosts(cache_path):
    with open(cache_path, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        sshurl = rows[1][1]

    # Get the ssh host part
    sshhost = "/".join(sshurl.split("/")[:3])

    # Get the web host part
    first_at_index = sshurl.index("@")
    second_colon_index = sshurl.index(":", first_at_index + 1)
    webhost = f"https://{sshurl[first_at_index + 1:second_colon_index]}"

    return sshhost, webhost

def write_csv(project_list):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(project_list)

def main():
    parser = argparse.ArgumentParser(description='Load GitLab projects and execute actions with Fzf.')
    parser.add_argument('--load', action='store_true', help=f'Load projects into {cache_path}')
    parser.add_argument('--env-file', help='Path to a .env file to load environment variables from.')
    args = parser.parse_args()

    # Load environment variables from file if specified
    if args.env_file:
        if os.path.exists(args.env_file):
            # print(f"Loading environment variables from {args.env_file}")
            dotenv.load_dotenv(dotenv_path=args.env_file)
        else:
            print(f"Warning: Specified env file '{args.env_file}' not found.", file=sys.stderr)

    if args.load or not os.path.isfile(cache_path):
        # Ensure GITLAB_TOKEN is available after potentially loading .env
        global GITLAB_TOKEN
        GITLAB_TOKEN = os.environ.get('GITLAB_TOKEN')
        projects = get_projects()
        write_csv(projects)

    sshhost, webhost = get_ssh_and_web_hosts(cache_path)

    command = f"""cat {cache_path} \
                 | sed 's/,[^,]*\/\/[^\/]*\//,/; s/\.[^.]*$//'  \
                 | column -t -s, \
                 | fzf --header-lines=1 \
                    --header "| enter:clone | ctrl-o:open |" \
                    --prompt="projects>"\
                    --height=80% \
                    --multi \
                    --preview-window right,hidden,60% \
                    --preview "aws ec2 describe-instances --instance-ids {{1}} | bat -l json --color always" \
                        --bind "enter:execute(git clone {sshhost}/{{2}}.git {basedir}/{{2}})" \
                        --bind "ctrl-o:execute-silent({open_bin} {webhost}/{{2}})+abort" \
                        --bind "ctrl-h:execute-silent(tmux select-pane -L)" \
                        --bind 'ctrl-space:toggle-preview'
                 """

    subprocess.run(command, shell=True)


if __name__ == "__main__":
    main()
