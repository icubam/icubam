import numpy as np
import tornado.web
import math
from collections import defaultdict

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.transform import dodge
from bokeh.models import ColumnDataSource

from icubam.db.store import to_pandas
from icubam.backoffice.handlers import base


class OperationalDashHandler(base.BaseHandler):
  ROUTE = '/operational-dashboard'

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    arg_region = self.get_query_argument('region', default=None)

    current_region = None
    current_region_name = "Toutes les régions"
    if arg_region is not None and arg_region.isdigit():
      try:
        current_region = self.db.get_region(int(arg_region))
        current_region_name = current_region.name
      except Exception:
        logging.warning(
          f"Invalid query argument: region={arg_region} "
          f"Falling back to all regions."
        )

    figures = []

    bed_counts = self.db.get_visible_bed_counts_for_user(self.user.user_id)

    bed_counts = to_pandas(bed_counts)

    if current_region is not None:
      mask = bed_counts['icu_region_id'] == current_region.region_id
      bed_counts = bed_counts[mask]

    agg_args = {
      key: 'sum'
      for key in [
        'n_covid_occ', 'n_covid_free', 'n_ncovid_occ', 'n_ncovid_free',
        'n_covid_deaths', 'n_covid_healed', 'n_covid_refused',
        'n_covid_transfered'
      ]
    }
    df = bed_counts.groupby('icu_city').agg(agg_args)

    df['total_capacity'] = df[[
      'n_covid_occ', 'n_covid_free', 'n_ncovid_occ', 'n_ncovid_free'
    ]].sum(axis=1)
    df['fraq_covid_occ'
       ] = 100 * df['n_covid_occ'] / (df['n_covid_occ'] + df['n_covid_free'])
    df['fraq_total_occ'] = 100 * (df['n_covid_occ'] +
                                  df['n_ncovid_occ']) / (df['total_capacity'])
    df['frac_covid_refused'
       ] = 100 * df['n_covid_refused'] / df['total_capacity']

    df = df.sort_values('fraq_covid_occ', ascending=False)

    df_sum = df.sum(axis=0).astype(int)

    metrics_layout = [
      [{
        'value': df_sum['n_covid_occ'],
        'label': 'Nbr. lits covid occupés'
      }, {
        'value': df_sum['n_covid_free'],
        'label': 'Nbr. lits covid dispo.'
      }, {
        'value': df_sum['n_covid_refused'],
        'label': 'Nbr. cas covid refusés'
      }],
      [{
        'value': df_sum['n_covid_deaths'],
        'label': 'Nbr. morts (cumulé)'
      }, {
        'value': df_sum['n_covid_healed'],
        'label': 'Nbr. gueris (cumulé).'
      }, {
        'value': df_sum['n_covid_transfered'],
        'label': 'Nbr. transferé (cumulé)'
      }],
    ]

    df_viz = ColumnDataSource.from_df(df.reset_index())

    p = figure(
      x_range=list(df.index),
      plot_height=400,
      sizing_mode="stretch_width",
    )
    p.xaxis.major_label_orientation = math.pi / 4
    p.y_range.start = 0
    p.yaxis.axis_label = 'Fraction (%)'

    p.vbar(
      x=dodge('index', 0.25, range=p.x_range),
      top='fraq_covid_occ',
      source=df_viz,
      width=0.2,
      alpha=0.8,
      legend_label="Taux de remplissage lits (covid)",
      color="#c9d9d3"
    )
    p.vbar(
      x=dodge('index', 0.50, range=p.x_range),
      top='fraq_total_occ',
      source=df_viz,
      width=0.2,
      alpha=0.8,
      legend_label="Taux de remplissage lits (total)",
      color="#718dbf",
    )
    p.vbar(
      x=dodge('index', 0.75, range=p.x_range),
      top='frac_covid_refused',
      source=df_viz,
      width=0.2,
      alpha=0.8,
      legend_label="Taux de refus (covid) / capacité totale",
      color="#e84d60",
    )
    p.legend.location = "center_left"
    p.legend.orientation = "vertical"
    p.legend.label_text_font_size = '7pt'
    p.legend.background_fill_alpha = 0.7

    script, div = components(p)
    figures.append(dict(script=script, div=div))

    regions = [{
      'name': el.name,
      'id': el.region_id
    } for el in self.db.get_regions()]
    regions = list(sorted(regions, key=lambda x: x['name']))

    self.render(
      "operational-dashboard.html",
      figures=figures,
      regions=regions,
      current_region_name=current_region_name,
      metrics_layout=metrics_layout
    )
