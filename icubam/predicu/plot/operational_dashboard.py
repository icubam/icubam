
from absl import logging
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.transform import dodge
from bokeh.models import ColumnDataSource
import functools
from itertools import zip_longest
import math
import os
import pandas as pd
from pathlib import Path
from typing import List, Tuple


from icubam.db.store import to_pandas, BedCount


def _prepare_data(bed_counts: pd.DataFrame) -> Tuple[pd.DataFrame, List]:
  """Make plot data"""
  agg_args = {
    key: 'sum'
    for key in [
      'n_covid_occ', 'n_covid_free', 'n_ncovid_occ', 'n_ncovid_free',
      'n_covid_deaths', 'n_covid_healed', 'n_covid_refused',
      'n_covid_transfered'
    ]
  }
  df: pd.DataFrame = bed_counts.groupby('icu_dept').agg(agg_args)

  df['total_capacity'] = df[[
    'n_covid_occ', 'n_covid_free', 'n_ncovid_occ', 'n_ncovid_free'
  ]].sum(axis=1)
  df['fraq_covid_occ'
     ] = 100 * df['n_covid_occ'] / (df['n_covid_occ'] + df['n_covid_free'])
  df['fraq_total_occ'] = 100 * (df['n_covid_occ'] +
                                df['n_ncovid_occ']) / (df['total_capacity'])
  df['frac_covid_refused'] = 100 * df['n_covid_refused'] / df['total_capacity']

  df = df.sort_values('fraq_covid_occ', ascending=False)

  df_sum = df.sum(axis=0).astype(int)

  metrics_layout = [
    [{
      'value': df_sum['n_covid_occ'],
      'label': ('Occupied COVID+ beds', )
    }, {
      'value': df_sum['n_covid_free'],
      'label': ('Available COVID+ beds', ),
    }, {
      'value': df_sum['n_covid_refused'],
      'label': ('Refused', '(due to unavailability)')
    }],
    [{
      'value': df_sum['n_covid_deaths'],
      'label': ('COVID deceased', )
    }, {
      'value': df_sum['n_covid_healed'],
      'label': ('COVID healed', ),
    }, {
      'value': df_sum['n_covid_transfered'],
      'label': ('Transfers', '(to other ICU)')
    }],
  ]
  return df, metrics_layout


def _make_bar_plot(df: pd.DataFrame, locale):
  """Generate a Bokeh figure"""
  df_viz = ColumnDataSource.from_df(df.reset_index())

  p = figure(
    x_range=list(df.index),
    plot_height=400,
    sizing_mode="stretch_width",
  )
  p.xaxis.major_label_orientation = math.pi / 4
  p.y_range.start = 0
  p.yaxis.axis_label = locale.translate("Rate (%)")

  p.vbar(
    x=dodge('index', 0.25, range=p.x_range),
    top='fraq_covid_occ',
    source=df_viz,
    width=0.2,
    alpha=0.8,
    legend_label=locale.translate("Beds utilization rate (covid)"),
    color="#0f2080"
  )
  p.vbar(
    x=dodge('index', 0.50, range=p.x_range),
    top='fraq_total_occ',
    source=df_viz,
    width=0.2,
    alpha=0.8,
    legend_label=locale.translate("Beds utilization rate (total)"),
    color="#85c0f9",
  )
  p.vbar(
    x=dodge('index', 0.75, range=p.x_range),
    top='frac_covid_refused',
    source=df_viz,
    width=0.2,
    alpha=0.8,
    legend_label=locale.translate("Rejection rate (covid) / total capacity"),
    color="#f5793a",
  )
  p.legend.location = "center_left"
  p.legend.orientation = "vertical"
  p.legend.label_text_font_size = '7pt'
  p.legend.background_fill_alpha = 0.7
  return p


def _grouper(iterable, n, fillvalue=None):
  """Collect data into fixed-length chunks or blocks

  Copied from https://docs.python.org/3.8/library/itertools.html#itertools-recipes
  
  Example
  -------
  >>> grouper('ABCDEFG', 3, 'x')
  ABC DEF Gxx
  """
  args = [iter(iterable)] * n
  return list(zip_longest(fillvalue=fillvalue, *args))


def _list_extra_plots(input_dir: Path) -> List[str]:
  """Return a list of available plot names"""
  if not isinstance(input_dir, Path):
    raise ValueError(f'input_dir={input_dir} must be a Path object')
  if not input_dir.exists():
    return []
  out = []
  for s in os.listdir(input_dir):
    fpath = Path(s)
    if fpath.suffix != '.png':
      continue
    out.append(fpath.stem)
  return list(sorted(out))


def make(
  user_id, db, region=None, locale=None, extra_plots_dir="", external=False
):
  current_region = None
  if locale is not None:
    current_region_name = locale.translate("All regions")
  else:
    current_region_name = "All regions"

  if region is not None and region.isdigit():
    try:
      current_region = db.get_region(int(region))
      current_region_name = current_region.name
    except Exception:
      logging.warning(
        f"Invalid query argument: region={region} "
        f"Falling back to all regions."
      )

  if not external:
    get_counts_fn = db.get_visible_bed_counts_for_user
  else:
    get_counts_fn = functools.partial(
      db.get_bed_counts_for_external_client, latest=True)

  figures = []
  bed_counts = get_counts_fn(user_id)
  if bed_counts:
    bed_counts = to_pandas(bed_counts)
    if current_region is not None:
      mask = bed_counts['icu_region_id'] == current_region.region_id
      bed_counts = bed_counts[mask]
  else:
    # when no data, make sure the resulting dataframe has
    # correct column names.
    columns = [key for key in dir(BedCount) if not key.startswith('_')]
    columns += ['icu_dept']
    bed_counts = pd.DataFrame([], columns=columns)

  df, metrics_layout = _prepare_data(bed_counts)

  p = _make_bar_plot(df, locale)

  script, div = components(p)
  figures.append(dict(script=script, div=div))

  plots_extra = _list_extra_plots(Path(extra_plots_dir))
  # stack two columns per row
  plots_extra = _grouper(plots_extra, 2)

  regions = [{'name': el.name, 'id': el.region_id} for el in db.get_regions()]
  regions = list(sorted(regions, key=lambda x: x['name']))

  return {
    'figures': figures,
    'regions': regions,
    'current_region_name': current_region_name,
    'metrics_layout': metrics_layout,
    'plots_extra': plots_extra
  }
