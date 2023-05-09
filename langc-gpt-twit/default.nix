with import <nixpkgs> {};

mkShell {
  name = "test";
  buildInputs = with python3Packages; [ venvShellHook ];
  venvDir = ".venv310";
  # fetchPypi not working for us
  # TODO: get modules from file requirements.txt so we set same version of all pkgs
  # # pass as variable so they are updated/loaded dynamically
  postShellHook = ''
    pip install openai deeplake langchain tiktoken
  '';
}
