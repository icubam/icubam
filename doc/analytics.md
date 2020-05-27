# Analytics server

The analytics server is responsible for handling data exports / imports
at the `/db/*` endpoints. It also includes a callback to re-generate dashboard
plots periodically.

## Rendering third party figures for the dashboard

To render external figures with the `/operational-dashboard` endpoint, the
`config.toml` used to run the server must contain a valid `extra_plots_dir`
entry, e.g.

```
[analytics]
  extra_plots_dir = "/tmp/dasboard_plots_dir"
  generate_plots_every = 3600  # in seconds
```

Any `.png` in this folder will then be displayed at the end of `/operational-dashboard`
page. Figures are sorted alphabetically: prepend a number to the figure file name for
a specific ordering. 


To generate these plots manually run,
```
python scripts/gen_plots.py --config=<config.toml>
```
