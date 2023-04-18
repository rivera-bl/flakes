# AWS SSO login with fzf

![fws](../_docs/images/fws.png "Image")

```bash
$ nix run "github:rivera-bl/flakes?dir=fws"

usage: main [-h] [-o] [-l]

AWS SSO login with fzf

options:
  -h, --help   show this help message and exit
  -o, --load   Cargar cuentas en /tmp/fws/accounts.csv y sso.sessions en ~/.aws/config
  -l, --login  Despliega `fzf` para seleccionar cuenta con la que iniciar sesión en AWS SSO.
               Si es primera vez que se ejecuta el comando, entonces va ejecutar
               automaticamente la función de --load, para obtener la lista de cuentas
```

````bash
$ aws --version                                                                                                                                                    4s
aws-cli/2.11.6 Python/3.10.10 Linux/5.15.90.1-microsoft-standard-WSL2 source/x86_64.nixos.23 prompt/off
````
