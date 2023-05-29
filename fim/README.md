# fim

````bash
$ nix run "github:rivera-bl/flakes?dir=fim"

Container Registry actions with fzf

options:
  -h, --help  show this help message and exit
  --load      Load ECR images into /tmp/fim/{account}_images.csv
  --local     Open LOCAL registry with fzf
  --ecr       Open ECR registry with fzf
````

## TODO

- [ ] fix ecr-credential-helper
  - or run the sudo podman login as an exception catch
- [ ] --bind inspect image (ctrl-v)
  - for this we have to pull the image first
- [ ] --bind open repository in browser (ctr-o)
- [ ] run get_account_id only when --ecr