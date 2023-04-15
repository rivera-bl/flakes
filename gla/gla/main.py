import os
import json
import subprocess
import sys
import gitlab

# TODO multi selection bindings
# TODO binding clone with namespace (exclude first group)
# TODO binding open in gitlab
# TODO binding copy id to clipboard

GITLAB_SERVER = os.environ.get('GL_SERVER', 'https://gitlab.com')
GITLAB_TOKEN = os.environ.get('GL_TOKEN')
cache_path  = '/tmp/gla/projects.csv'

def main():
    if not os.path.isfile(cache_path):
        if not GITLAB_TOKEN:
            print("Please set the GL_TOKEN env variable.")
            sys.exit(1)
        gl = gitlab.Gitlab(GITLAB_SERVER, GITLAB_TOKEN)
        gl.auth()

        # subprocess.Popen(['column', '-t', '-s,'], input=csv.encode('utf-8'), check=True)
        # projects = gl.projects.list(page=1, per_page=5)
        projects = gl.projects.list(all=True)
        csv = "id,name,ssh_url_to_repo\n"
        for project in projects:
            # print(json.dumps(project.attributes, indent=4, sort_keys=True))
            values = [
                str(project.id),
                project.name,
                project.ssh_url_to_repo
            ]
            csv += ','.join(values) + "\n"

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            f.write(csv)

    # use shell column command to convert csv variable into columns and pipe the result to fzf shell command
    csv     = subprocess.Popen(['cat', cache_path], stdout=subprocess.PIPE)
    columns = subprocess.Popen(['column', '-t', '-s,'], stdin=csv.stdout, stdout=subprocess.PIPE)
    fzf     = subprocess.Popen(['fzf', '--prompt=projects>', '--min-height=20', '--header-lines=1'], stdin=columns.stdout, stdout=subprocess.PIPE)

    selraw = fzf.stdout.read()
    if not selraw:
        exit()

    print(selraw.decode('utf-8'))