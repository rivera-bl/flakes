import subprocess

# Ejecutar el comando 'ls -l' en la shell
output = subprocess.check_output(['cat', 'cache', '|', 'fzf'])

# Imprimir la salida obtenida del comando 'ls -l'
print(output.decode('utf-8'))
