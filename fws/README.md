# AWS SSO login with fzf

![fws](../_docs/images/fws.png "Image")

```bash
$ nix run "github:rivera-bl/flakes?dir=fws"

AWS SSO Login with fzf

options:
  -h, --help            show this help message and exit
  --load sso_start_url  Load accounts in `/tmp/fws/accounts.csv` and sso.sessions in
                        `~/.aws/config`, takes `sso_start_url` as an argument
  --login               Pipe `/tmp/fws/accounts.csv` into FZF to select account to login
                        with AWS SSO
```

````bash
$ aws --version
aws-cli/2.11.6 Python/3.10.10 Linux/5.15.90.1-microsoft-standard-WSL2 source/x86_64.nixos.23 prompt/off
````

## Disclaimer

This is a personal project, so it may not work as expected. The first run of this script need to have an existing profile in `~/.aws/config` with the `sso_start_url` and `sso_region` configured. Then you can use `aws sso login --profile ${PROFILE_NAME}` to login to AWS SSO.

````toml
[profile XXXXXXXXXXXXXXXX]
sso_session = XXXXXXXXXXXXXXX
sso_account_id = XXXXXXXXXXXXXXX
sso_role_name = XXXXXXXXXXXXXXXXXX
region = us-east-1
output = json

[sso-session XXXXXXXXXXXXX]
sso_start_url = XXXXXXXXXXXXXXXXXXXX
sso_region = us-east-1
sso_registration_scopes = sso:account:access
````
