# # TODO add nix-shell with all pkgs (fzf, poetry)
# # TODO add docker image
{
  description = "Application packaged using poetry2nix";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.poetry2nix = {
    url = "github:nix-community/poetry2nix";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        inherit (import poetry2nix { inherit pkgs; }) mkPoetryApplication;
        pkgs = nixpkgs.legacyPackages.${system};
        lastModifiedDate = self.lastModifiedDate or self.lastModified or "19700101";
        version = builtins.substring 0 8 lastModifiedDate;
      in rec
      {
        packages = { myapp = mkPoetryApplication { projectDir = ./.; };
          default = self.packages.${system}.myapp;
        };

        devShells.default = pkgs.mkShell {
          packages = [ poetry2nix.packages.${system}.poetry ];
        };

        packages.docker = let
          mydocker = self.packages.${system}.default;
        in
          pkgs.dockerTools.buildLayeredImage {
            name = "fws";
            tag = version;
            # TODO make tmux optional
            # Why fzf adds 200mb?
            # mount .kube/ folder when running
            contents = [pkgs.findutils
                        pkgs.fzf
                        pkgs.bash
                        packages.myapp];
            };
            config = {
              Entrypoint = [ "/bin/fws" ];
              Cmd = ["/bin/fws"];
              WorkingDir = "/";
            };
      });
}
