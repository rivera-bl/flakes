import os
import re
import json
import subprocess
import sys
import gitlab

GITLAB_SERVER = os.environ.get('GL_SERVER', 'https://gitlab.com')
GITLAB_TOKEN = os.environ.get('GL_TOKEN')
cache_path  = '/tmp/gla/projects.csv'
open_bin = 'wsl-open'

def main():
    if not os.path.isfile(cache_path):
        if not GITLAB_TOKEN:
            print("Please set the GL_TOKEN env variable.")
            sys.exit(1)
        gl = gitlab.Gitlab(GITLAB_SERVER, GITLAB_TOKEN)
        gl.auth()

        # projects = gl.projects.list(page=1, per_page=5)
        projects = gl.projects.list(all=True)
        csv = "id,ssh_url_to_repo\n"
        for project in projects:
            # only exclude group if argument is passed
            if len(sys.argv) == 2:
                # if string before first '/' of project.path_with_namespace is not argument, then continue to the next iteration
                if project.path_with_namespace.split('/')[0] != sys.argv[1]: continue
            # print(json.dumps(project.attributes, indent=4, sort_keys=True))
            values = [
                str(project.id),
                project.ssh_url_to_repo
            ]
            csv += ','.join(values) + "\n"

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            f.write(csv)

    # use shell column command to convert csv into columns and pipe the result to fzf shell command
    csv     = subprocess.Popen(['cat', cache_path], stdout=subprocess.PIPE)
    columns = subprocess.Popen(['column', '-t', '-s,'], stdin=csv.stdout, stdout=subprocess.PIPE)
    fzf     = subprocess.Popen(['fzf',
                                '--prompt=projects>',
                                "--header=\ enter: clone \ ctrl-o: open \\",
                                '--min-height=20',
                                '--header-lines=1',
                                '--multi',
                                '--bind=enter:execute-multi(echo -n clone,{2})+abort',
                                '--bind=ctrl-o:execute(echo -n open,{2})+abort'
                                ], stdin=columns.stdout, stdout=subprocess.PIPE)
    selraw = fzf.stdout.read()
    if not selraw: exit()
    sel = selraw.decode('utf-8').split()

    if sel[0].startswith('clone'):
        for i in sel:
            url = i.replace('clone,', '')
            dir = url.replace('.git', '')
            for i in range(4):
                dir = dir[dir.find('/')+1:]
            # git clone sel into home user directory + code/gitlab + dir
            subprocess.run(['git', 'clone', url, os.path.expanduser('~/code/gitlab/') + dir])
    elif sel[0].startswith('open'):
        for i in sel:
            url = i.replace('open,', '').replace('ssh://git@', 'https://')
            # use regex to remove the port number
            url = re.sub(r':\d+/', '/', url)
            subprocess.run([open_bin, url])