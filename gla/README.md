# Gitlab Projects actions with FZF

Simple program to select gitlab projects to clone/open wit FZF. Use tab to select multiple entries.

```bash
# set the `GITLAB_SERVER` and `GITLAB_TOKEN` environment variables.
$ nix run "github:rivera-bl/flakes?dir=gla"
```

## Notes

It takes about a minute to load the repositories when there are over 1000+
