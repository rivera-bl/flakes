# Gitlab Projects actions with FZF

Simple program to select gitlab projects to clone/open wit FZF. Use tab to select multiple entries.
You can optionally pass an argument to exclude from the list every project whose namespace doesn't start with that name.

```bash
# set the `GL_SERVER` and `GL_TOKEN` environment variables.
$ nix run "github:rivera-bl/flakes?dir=gla"
```

## Notes

- It takes about a minute to load the repositories when there are over 1000+
- Set the GL_TOKEN and GL_SERVER variables directly on flakes/gla for faster testing
  -  poetry -C flakes/gla run gla
