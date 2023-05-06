import os
import argparse
import subprocess
import toml
import tomlkit
import pkg_resources
from jinja2 import Template

# TODO main.j2 help()
# TODO main.py template_flake()
# TODO main.py template_readme()
# # add flags for each section -> overview,run,versions
# # overview: output $command --help
# # run: nix,python3,docker
# # versions: python, poetry, nix, etc
# TODO main.py post() flag with tmux neww
# TODO pre-commit hook update README.md all sections

parser = argparse.ArgumentParser(description="Template Poetry")
parser.add_argument("--dir", required=True, help="Directory to create the project in")
parser.add_argument("--name", required=True, help="Name of the project")
parser.add_argument("--modules", required=True, nargs="+", help="List of modules to add to the project")
args = parser.parse_args()

def main():
  name = args.name.replace("-", "_").lower()
  template_poetry(args.dir, name, args.modules)

def template_poetry(dir, name, modules):
  dir = os.path.join(dir, name)
  if os.path.exists(dir):
    print("Directory already exists")
    return

  subprocess.run(["poetry", "new", dir, "--src"])
  for module in modules:
      subprocess.run(["poetry", "add", module, "-C", dir])

  with open(dir + "/pyproject.toml", "r") as f:
      config = toml.load(f)

  config["tool"]["poetry"]["scripts"] = {
    'main': name + '.main:main'
  }
  config["virtualenvs"] = {
    "in-project": True
  }
  config["tool"]["poetry"]["name"] = name

  # append to pyproject file
  with open(dir + '/pyproject.toml', 'w') as f:
    f.write('\n')
    toml.dump(config, f)

  subprocess.run(["poetry", "install", "-C", dir])
  template_main(dir, name, modules)

def template_main(dir, name, modules):
    main_dir=os.path.join(dir, "src", name)

    template_content = pkg_resources.resource_string(__name__, "main.j2").decode()

    template = Template(template_content)

    # # Generate the import statements
    imports = "\n".join([f"import {module}" for module in modules])

    # # Render the template
    file_contents = template.render(imports=imports)

    with open(main_dir + "/main.py", "w") as f:
        f.write(file_contents)
