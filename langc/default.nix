with import <nixpkgs> { };
let
  filePath = builtins.toString ./. + "/requirements.txt";
  pipModules = builtins.replaceStrings [ "\n" ] [ " " ] (builtins.readFile filePath);
in
mkShell {
  name = "langc";
  buildInputs = with python3Packages; [ venvShellHook ];
  venvDir = ".venv-langc";
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib"; # needed for langchain
  postShellHook = ''
    pip install -q --disable-pip-version-check ${pipModules}
    unset KUBECONFIG
    printf "\033c"
    echo -e "\n${pipModules}"
  '';
}
