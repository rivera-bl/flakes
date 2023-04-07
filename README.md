# Flakes

some programs

````bash
# .git/hooks/post-commit
paths="fws/fws/main.py kfc/kfc.sh"
modified_files=$(git diff --name-only HEAD^ HEAD)

ismodified=false
for file in $modified_files
do
  for path in $paths
  do
    if [[ $file == $path ]]
    then
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
