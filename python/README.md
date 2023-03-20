## Package Python script with Poetry and Flakes

1. init project

````bash
poetry new ${project}
poetry install        # flakes needs the poetry.lock
````
2. add script

````toml
# pyproject.toml
[tool.poetry.scripts]
start = "${project}.main:start"
````

3. create script

````python
# ${project}/main.py
def start():
    print("hello nix")
````

4. run script

````bash
poetry run start
````
