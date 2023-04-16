# Gitlab Projects actions with FZF

Simple program to select gitlab projects to clone/open wit FZF. Use tab to select multiple entries.
You can optionally pass an argument to exclude from the list every project whose namespace doesn't start with that name.

```bash
# set the `GL_SERVER` and `GL_TOKEN` environment variables.
$ nix run "github:rivera-bl/flakes?dir=gla"
```