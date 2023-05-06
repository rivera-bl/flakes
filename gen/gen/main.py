import os
import argparse
import subprocess
import boto3
import toml

parser = argparse.ArgumentParser(description="Template Poetry")
parser.add_argument("--dir", required=True, help="Directory to create the project in")
parser.add_argument("--name", required=True, help="Name of the project")
parser.add_argument("--modules", required=True, nargs="+", help="List of modules to add to the project")
args = parser.parse_args()

# home        = os.path.expanduser("~/")

def main():
    template_poetry(args.dir, args.name, args.modules)

def template_poetry(dir, name, modules):
  dir = "/".join([dir, name]) + "/"
  if os.path.exists(dir):
    print("Directory already exists")
    return

  subprocess.run(["poetry", "new", dir])
  for module in modules:
      subprocess.run(["poetry", "add", module, "-C", dir])

  config = {}
  config['tool.poetry.scripts'] = {
    'main': name + '.main:main'
  }
  config['virtualenvs'] = {
    'in-project': 'true'
  }

  # append to pyproject file
  with open(dir + 'pyproject.toml', 'a') as f:
    f.write('\n')
    toml.dump(config, f)

  subprocess.run(["poetry", "install", "-C", dir])