# Flakes

some programs

````bash
# .git/hooks/post-commit
paths="fws/fws/main.py kfc/kfc.sh"
# Obtener la lista de archivos modificados
modified_files=$(git diff --name-only HEAD^ HEAD)

# Verificar si los archivos modificados están en $paths
ismodified=false
for file in $modified_files
do
  echo $file
  for path in $paths
  do
    echo $path
    if [[ $file == $path ]]
    then
      echo "modified"
      ismodified=true
      break 2
    fi
  done
done

if [ "$ismodified" = true ]; then
  git push
  cd ~/code/personal/system
# TODO fix to only update this.flakes repo
  nix flake update
  sudo nixos-rebuild switch --flake ~/code/personal/system/#
fi
````
