# Command Line Interface (CLI)

## icubam.predicu
<!-- The following help needs to be manually regenerated
  with <script> help as long as we keep a documentaton in markdown
-->

**icubam.predicu export**
```
$ python -m icubam.predicu export --help
Usage: __main__.py export [OPTIONS]

Options:
  -o, --output-dir TEXT
  --api-key TEXT
  --spread-cum-jump-correction BOOLEAN
  --icubam-host TEXT
  --max-date TEXT                 max date of the exported data (e.g.
                                  2020-04-05)

  --help                          Show this message and exit.
```

**icubam.predicu make_dashboard_plots**
```
$ python -m icubam.predicu make_dashboard_plots --help
Usage: __main__.py make_dashboard_plots [OPTIONS]

  Make dasboard plots

Options:
  -o, --config TEXT      ICUBAM config file.  [required]
  -o, --output-dir TEXT  Output directory where to store plots. If not
                         provided config.analytics.extra_plots_dir is used.

  --help                 Show this message and exit.
```


**icubam.predicu plot**
```
$ python -m icubam.predicu plot --help
Usage: __main__.py plot [OPTIONS] [PLOTS]...

  Specific plots to generate (all are by default).

Options:
  --api-key TEXT
  --icubam-host TEXT
  --matplotlib-style TEXT         matplotlib style used in generated plots.
  -o, --output-dir TEXT           Directory where the resulting plots will be
                                  stored.

  --output-type, --output-type [tex|png|pdf]
  --restrict-to-region TEXT       Whether to restrict the data a region. Valid
                                  values are: Grand-Est.

  --help                          Show this message and exit.
  ```
