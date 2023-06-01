import os
import subprocess
import sys
import gitlab
import csv
import argparse

GITLAB_SERVER = os.environ.get('GL_SERVER', 'https://gitlab.com')
GITLAB_TOKEN = os.environ.get('GL_TOKEN')
cache_path = '/tmp/gla/projects.csv'
open_bin = 'wsl-open'

def get_projects():
    if not GITLAB_TOKEN:
        print("Please set the GL_TOKEN env variable.")
        sys.exit(1)
    gl = gitlab.Gitlab(GITLAB_SERVER, GITLAB_TOKEN)
    gl.auth()

    projects = gl.projects.list(per_page=7, all=False)
    project_list = []

    # Add the header to the project_list
    header = ['Id', 'Repository']
    project_list.append(header)

    for project in projects:
        project_info = [str(project.id), project.ssh_url_to_repo]
        project_list.append(project_info)
    return project_list

def write_csv(project_list):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(project_list)

def main():
    parser = argparse.ArgumentParser(description='Load GitLab projects and execute actions with Fzf.')
    parser.add_argument('--load', action='store_true', help=f'Load projects into {cache_path}')
    args = parser.parse_args()

    command = f"""cat {cache_path} \
                 | sed 's/,[^,]*\/\/[^\/]*\//,/; s/\.[^.]*$//'  \
                 | column -t -s, \
                 | fzf --header-lines=1 \
                    --header "| enter:clone | ctrl-o:open |" \
                    --prompt="projects>"\
                    --height=80% \
                    --preview-window right,hidden,60% \
                    --preview "aws ec2 describe-instances --instance-ids {{1}} | bat -l json --color always" \
                        --bind "ctrl-h:execute-silent(tmux select-pane -L)" \
                        --bind 'ctrl-space:toggle-preview'
                 """

    if args.load or not os.path.isfile(cache_path):
        projects = get_projects()
        write_csv(projects)

    subprocess.run(command, shell=True)


if __name__ == "__main__":
    main()
