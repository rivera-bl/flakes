## Package Python script with Poetry and Flakes

1. init project

````bash
poetry new ${project}
cd ${project}
poetry install              # flakes needs the poetry.lock
poetry add ${python-module} # adds python modules to poetry.lock
````
2. add script

````toml
# pyproject.toml
[tool.poetry.scripts]
main = "${project}.main:main"
````

3. create script

````python
# ${project}/main.py
def main():
    print("hello nix")
````

4. run script

````bash
poetry run main
````

5. nix

````bash
git add .
nix build   # locally build application
nix develop # devshell
nix run     # run application
````

6. lsp

to have lsp support for external dependencies, like boto3 or gitlab

````toml
# pyproject.toml
[virtualenvs]
in-project = true
````

## TODO

- [ ] single flake for all scripts? they look the same
