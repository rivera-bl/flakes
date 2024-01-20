{
  description = "crossplane-migrator";
  # can also be set system wide, see:
  # https://nixos.org/manual/nix/unstable/command-ref/conf-file.html#conf-bash-prompt
  nixConfig.bash-prompt = "\[nix-develop\]$ ";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
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
        pname = "crossplane-migrator";
        version = "v0.11.0";

        src = pkgs.fetchFromGitHub {
          owner = "crossplane-contrib";
          repo = pname;
          rev = version;
          sha256 = "sha256-2GJi3E7UQ1KQfk+G0NjOqQmsUFOUE6kAJckTcwg6re0=";
        };

        # vendorSha256 = pkgs.lib.fakeSha256;
        vendorSha256 = "sha256-4KUOfrbYFMj3x6LaGy5aawGNK41jrZTwbyeejWcknE0=";
      };

      packages.docker = let
        docker = self.packages.${system}.default;
      in
        pkgs.dockerTools.buildLayeredImage {
          name = docker.pname;
          tag = docker.version;
          contents = [docker];

          config = {
            Cmd = ["/bin/crossplane-migrator"];
            WorkingDir = "/";
          };
        };

      # devShells.default = with pkgs; # avoid writing pkgs.mkShell, pkgs.go ..
      
      #   mkShell {
      #     buildInputs = [go gopls gotools go-tools];
      #   };
    });
}
