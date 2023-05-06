import fileinput
import os
import argparse
import subprocess
import toml
import pkg_resources
from jinja2 import Template

# TODO main.py template_readme()
# TODO main.j2 argparse
# TODO main.j2 prompt()
# # add flags for each section -> overview,run,versions
# # overview: output $command --help
# # run: nix,python3,docker
# # versions: python, poetry, nix, etc
# TODO main.py post() flag with tmux neww
# TODO pre-commit hook update README.md all sections

dir = "/home/wim/code/personal/flakes"

parser = argparse.ArgumentParser(description="Template Poetry")
parser.add_argument("--dir", default=dir, required=False, help="Directory to create the project in")
parser.add_argument("--name", required=True, help="Name of the project")
parser.add_argument("--modules", required=True, nargs="+", help="List of modules to add to the project")
args = parser.parse_args()

def main():
  name = args.name.replace("-", "_").lower()
  template_poetry(args.dir, name, args.modules)

# template poetry commands,toml
def template_poetry(dir, name, modules):
  dir = os.path.join(dir, name)
  if os.path.exists(dir):
    print("Directory already exists")
    return

  # new project
  subprocess.run(["poetry", "new", dir, "--src"])
  # add modules
  for module in modules:
      subprocess.run(["poetry", "add", module, "-C", dir])

  # modify pyproject.toml file
  with open(dir + "/pyproject.toml", "r") as f:
      config = toml.load(f)

  config["tool"]["poetry"]["name"] = name
  config["tool"]["poetry"]["scripts"] = { 'main': name + '.main:main' }
  config["virtualenvs"] = { "in-project": True }

  with open(dir + '/pyproject.toml', 'w') as f:
    f.write('\n')
    toml.dump(config, f)

  # install project
  subprocess.run(["poetry", "install", "-C", dir])
  template_main(dir, name, modules)
  template_readme(dir, name)
  template_flake(dir)

# template main.py
def template_main(dir, name, modules):
    main_dir=os.path.join(dir, "src", name)

    template_content = pkg_resources.resource_string(__name__, "main.j2").decode()
    template = Template(template_content)
    imports = "\n".join([f"import {module}" for module in modules])
    file_content = template.render(imports=imports)

    with open(main_dir + "/main.py", "w") as f:
        f.write(file_content)

def template_readme(dir, name):
    readme_dir=os.path.join(dir, "README.md")

    template_content = pkg_resources.resource_string(__name__, "README.j2").decode()
    template = Template(template_content)
    file_content = template.render(name=name)

    with open(readme_dir, "w") as f:
        f.write(file_content)

def template_flake(dir):
  tpl_ver = "e1ccedce9b4f58422aa6588843c2995c74d796fd"
  subprocess.run(["nix", "flake", "init", "--template", f"github:nix-community/poetry2nix/{tpl_ver}"], cwd=dir)

  # replace "self" with "./." or nix cmds fail
  with fileinput.FileInput(dir + '/flake.nix', inplace=True, backup='.bak') as file:
      for line in file:
          if 'projectDir' in line:
              line = line.replace('self', './.')
          print(line, end='')

  # TODO build,dev,run working
