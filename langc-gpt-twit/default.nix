with import <nixpkgs> { };

let
  filePath = builtins.toString ./. + "/requirements.txt";
  pipModules = builtins.replaceStrings [ "\n" ] [ " " ] (builtins.readFile filePath);
in
mkShell {
  name = "langc-gpt-twit";
  buildInputs = with python3Packages; [ venvShellHook ];
  venvDir = ".venv-langc-gpt-twit";
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib"; # needed for langchain
  postShellHook = ''
    pip install ${pipModules}
    set -o vi
  '';
}
