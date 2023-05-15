{
  description = "A basic gomod2nix flake";

  # nixos-unstable
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/f00994e78cd39e6fc966f0c4103f908e63284780";
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.gomod2nix.url = "github:nix-community/gomod2nix";

  outputs = { self, nixpkgs, flake-utils, gomod2nix }:
    (flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ gomod2nix.overlays.default ];
          };
          iamlive = pkgs.buildGoApplication rec {
            pname = "iamlive";
            version = "0.52.0";
            modules = ./gomod2nix.toml;

            src = pkgs.fetchFromGitHub {
              owner = "iann0036";
              repo = "iamlive";
              rev = "v${version}";
              sha256 = "sha256-aTcateRe5dsSRAnLo3g4tFshuZ6nfC75er7iBGGqe0E=";
            };

            # This hash locks the dependencies of this package. It is
            # necessary because of how Go requires network access to resolve
            # VCS.  See https://www.tweag.io/blog/2021-03-04-gomod2nix/ for
            # details. Normally one can build with a fake sha256 and rely on native Go
            # mechanisms to tell you what the hash should be or determine what
            # it should be "out-of-band" with other tooling (eg. gomod2nix).
            # To begin with it is recommended to set this, but one must
            # remeber to bump this hash when your dependencies change.
            #vendorSha256 = pkgs.lib.fakeSha256;

            vendorSha256 = "sha256-KQr0DtyH3xzlFwsDl3MGLRRLQC4+EtdTOG7IhmNCzV4=";
          };

        in
        {
          packages.default = iamlive;
          devShells.default = import ./shell.nix { inherit pkgs; };
        })
    );
}
