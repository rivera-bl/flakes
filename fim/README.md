# fim

````bash
$ nix run "github:rivera-bl/flakes?dir=fim"

Container Registry actions with fzf

options:
  -h, --help  show this help message and exit
  --load      Load ECR images into `/tmp/fim/{account}_images.csv`
  --local     Open `local` registry with fzf
  --ecr       Open `ecr` registry with fzf
````

## TODO

- [ ] !!run get_account_id only when --ecr
- [ ] fix ecr-credential-helper
  - or run the {container} login as an exception catch
- [ ] --bind inspect image (ctrl-v)
  - for this we have to pull the image first
