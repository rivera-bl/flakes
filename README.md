# Flakes

some programs

````bash
# .git/hooks/post-commit
git push
cd ~/code/personal/system
# TODO fix to only update this.flakes repo
nix flake update
sudo nixos-rebuild switch --flake ~/code/personal/system/#
````


