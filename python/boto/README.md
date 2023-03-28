# Functions with AWS boto3

## Advantages over sh

### SSO login

#### Shell

````bash
_fzf_aws_sso_copy_url(){
  export ACCESS_TOKEN=$(cat $(\ls -1d ~/.aws/sso/cache/* | grep -v botocore) | head -n 1 | jq -r "{accessToken} | .[] | select( . != null )" | head -n 1)
  aws sso list-accounts --access-token ${ACCESS_TOKEN}
  # jq nonsense..
}
````

### Python
