{
  description = "iamlive";
  # can also be set system wide, see:
  # https://nixos.org/manual/nix/unstable/command-ref/conf-file.html#conf-bash-prompt
  nixConfig.bash-prompt = "\[nix-develop\]$ ";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-21.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      # lastModifiedDate = self.lastModifiedDate or self.lastModified or "19700101";
      # version = builtins.substring 0 8 lastModifiedDate;
      pkgs = import nixpkgs {inherit system;};
    in {
      packages.default = pkgs.buildGoModule rec {
        pname = "iamlive";
        version = "v1.1.12";

        src = pkgs.fetchFromGitHub {
          owner = "iann0036";
          repo = pname;
          rev = version;
          sha256 = "sha256-nVeFA2PVCkqegG5QSct+SGNRCQYCVJVaOh4HHTs2It0=";
        };

        vendorHash = null;
        vendorSha256 = null;
      };

      packages.docker = let
        docker = self.packages.${system}.default;
      in
        pkgs.dockerTools.buildLayeredImage {
          name = docker.pname;
          tag = docker.version;
          contents = [docker];

          config = {
            Cmd = ["/bin/iamlive"];
            WorkingDir = "/";
          };
        };

      # devShells.default = with pkgs; # avoid writing pkgs.mkShell, pkgs.go ..
      
      #   mkShell {
      #     buildInputs = [go gopls gotools go-tools];
      #   };
    });
}
