# Backoffice server


## Rendering third party figures in /operational-dashboard

To render external figures with the `/operational-dashboard` endpoint, the
`config.toml` used to run the server must contain a valid `extra_plots_dir`
entry, e.g.

```
[backoffice]
  extra_plots_dir = "/tmp/dasboard_plots_dir"
```

Any `.png` in this folder will then be displayed at the end of `/operational-dashboard`
page. Figures are sorted alphabetically: prepend a number to the figure file name for
a specific ordering. 
