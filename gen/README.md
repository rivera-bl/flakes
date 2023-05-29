# Generate Python Poetry projects with Flakes

```bash
nix run "github:rivera-bl/flakes?dir=gen" --dir /my/project/route --name myproject --modules module1 module2
```

dir is optional

````bash
cd /home/wim/code/personal/flakes/gen
poetry run main --name {myproj} --modules boto3
cd /home/wim/code/personal/flakes/{myproj}
poetry install
poetry run main
````
