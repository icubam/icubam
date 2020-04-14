import datetime
import json

import matplotlib.gridspec
import matplotlib.lines
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd

import predicu.data
import predicu.plot

import sys

data_source = "combined_icubam_public"

def slid_window_avg(a, wi):
  a_smoothed=np.zeros(a.shape)
  # for shift in range(1,wi):
  for i in range(len(a)):
    a_smoothed[i] += np.sum(a[i:i+wi])/ (a[i:i+wi]).shape[0]
  return a_smoothed


def compute_all_for_plots_by_dept(d, dep):
  dep_data = d[d["department"] == dep]
  dep_data = dep_data.sort_values(by="date")
  zeros = dep_data['n_covid_deaths']*0.0

  wi = 2 # sliding window time average

  ## flux covid (hopital, rea)
  flow_hopital_covid = slid_window_avg((dep_data[ set(["n_hospitalised_patients", "n_hospital_death", "n_hospital_healed"])     ].sum(axis=1)).diff(1).fillna(0),wi)
  flow_reanima_covid = slid_window_avg((dep_data[ set(['n_covid_deaths', 'n_covid_healed', 'n_covid_transfered','n_covid_occ']) ].sum(axis=1)).diff(1).fillna(0),wi)
  # flow_hopital_covid_region += np.array(flow_hopital_covid)
  # flow_reanima_covid_region += np.array(flow_reanima_covid)

  ## flux non-covid (hopital, rea)
  flow_hopital_n_cov = zeros # calculable a partir des data SOS medecin ?
  ## donnees SOS medecin:
  # nbre_pass_corona    -> passage aux urgences liés au corona (par age)
  # nbre_pass_tot       -> passage aux urgences (total)        (par age)
  # nbre_hospit_corona  -> envoi à l'hopital, lié au corona    (par age)
  flow_reanima_n_cov = zeros # il nous manque les flux sortants (morts, rad) de la rea non-covid


  wi = 3 # sliding window time average

  ## lits covid (hopital, rea)
  numberBed_hopital_covid_occup = slid_window_avg(dep_data.n_hospitalised_patients, wi)
  percenBed_hopital_covid_occup = 100*zeros # dep_data.n_hospitalised_patients / unknown
  percenBed_reanima_covid_occup = 100*slid_window_avg(dep_data.n_covid_occ / (dep_data.n_covid_occ + dep_data.n_covid_free), wi)

  ## lits non-covid (hopital, rea)
  numberBed_hopital_n_cov_occup = zeros # unknown
  percenBed_hopital_n_cov_occup = 100*zeros # unknown / unknown
  percenBed_reanima_n_cov_occup = 100*slid_window_avg(dep_data.n_ncovid_occ / (dep_data.n_ncovid_occ + dep_data.n_ncovid_free), wi)

  return flow_hopital_covid, flow_reanima_covid, \
      numberBed_hopital_covid_occup, percenBed_hopital_covid_occup, percenBed_reanima_covid_occup, \
      flow_hopital_n_cov, flow_reanima_n_cov, \
      numberBed_hopital_n_cov_occup, percenBed_hopital_n_cov_occup, percenBed_reanima_n_cov_occup



def plot_one_dep(d, dep):
  if dep in d["department"].unique():
    flow_hopital_covid, flow_reanima_covid, \
    numberBed_hopital_covid_occup, percenBed_hopital_covid_occup, percenBed_reanima_covid_occup, \
    flow_hopital_n_cov, flow_reanima_n_cov, \
    numberBed_hopital_n_cov_occup, percenBed_hopital_n_cov_occup, percenBed_reanima_n_cov_occup = compute_all_for_plots_by_dept(d, dep)

    dep_data = d[d["department"] == dep]
    dep_data = dep_data.sort_values(by="date")

    # plt.figure()
    # predicu.plot.DEPARTMENT_GRAND_EST_COLOR[dep]
    hospcolor = 'blue'
    hospmarker = "+"

    reacolor = 'red'
    reamarker  = "*"
    x_days = [date.strftime("%d-%m") for date in sorted(dep_data.date.unique())]

    fig, axs = plt.subplots(2, 1)
    # fig.set_figwidth(13)
    # fig.set_figheight(8)
    fig.set_figwidth(7)
    fig.set_figheight(8)
    # fig.suptitle(dep)
    axs[0].set_title(dep+": dynamique des flux entrants (covid)")
    axs[0].set_ylabel("nombre d'admission")
    axs[0].plot(x_days, flow_hopital_covid, label= "nombre d'admission à l'hopital pour covid+ (secteur+réa)", color=hospcolor, marker=hospmarker, lw=3, ls="-")
    axs[0].plot(x_days, flow_reanima_covid, label= "nombre d'admission en réanimation pour covid+"           , color=reacolor,  marker=reamarker,  lw=3, ls="--")
    axs[0].legend(handlelength=4,  loc='best') # bbox_to_anchor=(0, 0.1 ),
    axs[0].set_xticks(x_days[::3])

    axs[1].set_title(dep+": niveau de saturation des lits d'hospitalisation") # (covid)")
    axs[1].set_ylabel('nombre de lits', color="indigo")
    axs[1].tick_params(axis='y' , labelcolor="indigo")
    axs[1].plot(x_days, numberBed_hopital_covid_occup, label= 'nombre lits occupés hopital covid+  (secteur+réa)',  color="indigo", marker=hospmarker, lw=3, ls='-')
    ax2 = axs[1].twinx()  # instantiate a second axes that shares the same x-axis
    ax2.set_ylabel('pourcentage occupation lits', color=reacolor)  # we already handled the x-label with axs[1]
    ax2.tick_params(axis='y', labelcolor=reacolor)
    # ax2.plot(x_days, percenBed_hopital_covid_occup, label= '% lits occupés hopital covid+  (secteur+réa)', color=reacolor, marker=reamarker, lw=2, ls="-")
    ax2.plot(x_days, percenBed_reanima_covid_occup, label= '% lits occupés réanimation covid+', color=reacolor, marker=reamarker, lw=2, ls="--")
    ax2.plot(x_days, percenBed_reanima_n_cov_occup, label= '% lits occupés réanimation covid- (NON COV)', color=reacolor, lw=2, ls=":")
    h1, l1 = axs[1].get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axs[1].legend(h1+h2, l1+l2, handlelength=4, loc='best')
    axs[1].set_xticks(x_days[::3])
    # legend(handlelength=4,  loc='center left') # bbox_to_anchor=(0, 0.1 ),


    # axs[0,1].set_title("dynamique des flux entrants (non covid)")
    # axs[0,1].set_ylabel("nombre d'admission")
    # axs[0,1].plot(x_days, flow_hopital_n_cov, label= "nombre d'admission à l'hopital pour covid- (secteur+réa)", color=hospcolor, marker=hospmarker, lw=3, ls="-")
    # axs[0,1].plot(x_days, flow_reanima_n_cov, label= "nombre d'admission en réanimation pour covid-"           , color=reacolor,  marker=reamarker,  lw=3, ls="--")
    # axs[0,1].legend(handlelength=4,  loc='upper left') # bbox_to_anchor=(0, 0.1 ),


    # axs[1,1].set_title("niveau de saturation des lits d'hospitalisation (non covid)")
    # axs[1,1].set_ylabel('nombre de lits', color="indigo")
    # axs[1,1].tick_params(axis='y' , labelcolor="indigo")
    # axs[1,1].plot(x_days, numberBed_hopital_n_cov_occup, label= 'nombre occupés hopital covid-  (secteur+réa)',  color="indigo", marker=hospmarker, lw=3, ls='-')
    # ax2 = axs[1,1].twinx()  # instantiate a second axes that shares the same x-axis
    # ax2.set_ylabel('pourcentage occupation lits', color=reacolor)  # we already handled the x-label with axs[1,1]
    # ax2.tick_params(axis='y', labelcolor=reacolor)
    # # ax2.plot(x_days, percenBed_hopital_n_cov_occup, label= '% lits occupés hopital covid-  (secteur+réa)', color=reacolor, marker=reamarker, lw=2, ls="-")
    # ax2.plot(x_days, percenBed_reanima_n_cov_occup, label= '% lits occupés réanimation covid-', color=reacolor, marker=reamarker, lw=2, ls="--")
    # h1, l1 = axs[1,1].get_legend_handles_labels()
    # h2, l2 = ax2.get_legend_handles_labels()
    # axs[1,1].legend(h1+h2, l1+l2, handlelength=4, loc='best')


    fig.set_tight_layout(tight=True)
    fig.savefig(dep+".pdf")
    fig.savefig(dep+".png")
    return fig
  else:
    print(dep, ' is not a valid departement name')
    return None



## TODO: mettre le departement number en argument de cettte fonction
  # flow_hopital_covid_region = np.zeros(d["date"].unique().size) ## en esperant que les dates sont toutes alignees
  # flow_reanima_covid_region = np.zeros(d["date"].unique().size) ## en esperant que les dates sont toutes alignees
  # # flow_hopital_covid_region = pd.DataFrame(d["date"].unique() )
  # # flow_hopital_covid_region["date"] = d["date"].unique()
  # # flow_hopital_covid_region["totalDep"] = np.zeros(d["date"].unique().size)
  # # plt.figure(figsize=[10,5])

  # assert(d["department_pop"].unique().size == d["department"].unique().size )
  # pop_region = d["department_pop"].unique().sum() # populationde la region

  # ## explication : ##
  # assert( (d.n_covid_occ + d.n_ncovid_occ - d.n_icu_patients_icubam).sum() == 0 )
  # d.n_icu_patients_icubam == d.n_covid_occ + d.n_ncovid_occ

  # first we get the total for the region
  # for dep in d["department"].unique():


def plot(d):
  for dep in d["department"].unique():
    plot_one_dep(d, dep)
    # plt.show()

def plot_one_region(d, reg):
  pass
  # fig = plt.figure(figsize=[10,5])
  # plt.title("region")
  # plt.plot(dep_data["date"], slid_window_avg(flow_hopital_covid_region,wi), label= 'flux entrant hopital (régional, TOTAL)',          lw=2, color="blue", marker=hospmarker)
  # plt.plot(dep_data["date"], slid_window_avg(flow_reanima_covid_region,wi),   label= 'flux entrant réanim. (régional, TOTAL) (icubam)', lw=2, color="red", marker=reamarker)
  # plt.legend(loc='best')
  # plt.savefig("region-total.pdf")
  # plt.savefig("region-total.png")


api_key= "ecff5f8874c011eab17b005056b5c1bb"
# api_key = sys.argv[1]

# d = predicu.data.load_combined_icubam_public(api_key=api_key)
# print('data chargee')

plot(d)
plt.show()

# plot_one_dep(d, dep)
