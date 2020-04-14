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


## TODO: mettre le departement number en argument de cettte fonction
def plot(d):
  flow_public_hosp_region = np.zeros(d["date"].unique().size) ## en esperant que les dates sont toutes alignees
  flow_covidPlus_region = np.zeros(d["date"].unique().size) ## en esperant que les dates sont toutes alignees
  # flow_public_hosp_region = pd.DataFrame(d["date"].unique() )
  # flow_public_hosp_region["date"] = d["date"].unique()
  # flow_public_hosp_region["totalDep"] = np.zeros(d["date"].unique().size)
  # plt.figure(figsize=[10,5])
  assert(d["department_pop"].unique().size == d["department"].unique().size )
  pop_region = d["department_pop"].unique().sum() # populationde la region

  wi = 3 # sliding window time average

  # first we get the total for the region
  for dep in d["department"].unique():
    dep_data = d[d["department"] == dep]
    dep_data = dep_data.sort_values(by="date")

    flow_public_hosp = (dep_data[ set(["n_hospitalised_patients", "n_hospital_death", "n_hospital_healed"])     ].sum(axis=1)).diff(1).fillna(0)
    flow_covidPlus =   (dep_data[ set(['n_covid_deaths', 'n_covid_healed', 'n_covid_transfered','n_covid_occ']) ].sum(axis=1)).diff(1).fillna(0)
    flow_public_hosp_region += np.array(flow_public_hosp)
    flow_covidPlus_region += np.array(flow_covidPlus)


  for dep in d["department"].unique():
    dep_data = d[d["department"] == dep]
    dep_data = dep_data.sort_values(by="date")

    flow_public_hosp = (dep_data[ set(["n_hospitalised_patients", "n_hospital_death", "n_hospital_healed"])     ].sum(axis=1)).diff(1).fillna(0)
    flow_covidPlus =   (dep_data[ set(['n_covid_deaths', 'n_covid_healed', 'n_covid_transfered','n_covid_occ']) ].sum(axis=1)).diff(1).fillna(0)


    plt.figure(figsize=[13,5])
    plt.title(dep)
    # predicu.plot.DEPARTMENT_GRAND_EST_COLOR[dep]
    reamarker  = "*"
    hospmarker = "+"
    plt.plot(dep_data["date"], slid_window_avg(flow_public_hosp_region*dep_data["department_pop"]/pop_region,wi), label= 'flux entrant hopital (régional, pondéré)', lw=1, color="blue", marker=hospmarker)
    plt.plot(dep_data["date"], slid_window_avg(flow_covidPlus_region*dep_data["department_pop"]/pop_region,wi), label= 'dont réa. covid+ (icubam)', lw=1, color="red", marker=reamarker)

    plt.plot(dep_data["date"], slid_window_avg(flow_public_hosp,wi), label= 'flux entrant hopital', color="blue", marker=hospmarker, lw=3)
    # plt.plot(dep_data["date"], slid_window_avg(,wi), label= 'dont toute réa (pub) '         , color="red",  marker=reamarker,  lw=3) # info pas disponible
    # plt.plot(dep_data["date"], slid_window_avg(,wi), label= 'dont toute réa (icubam) '      , color="red",  marker=reamarker,  lw=3) # info pas disponible
    plt.plot(dep_data["date"], slid_window_avg(flow_covidPlus,1), label= 'dont réa covid+ (icubam) (non lissé)' , color="red",  marker=reamarker,  lw=3)

    # plt.plot(        dep_data["date"], slid_window_avg(dep_data.n_hospitalised_patients  ,wi) ,                                                     label= 'lits occupés (hopital)',  color="indigo", marker=hospmarker, lw=3, ls='--')
    plt.plot(        dep_data["date"], slid_window_avg(dep_data.n_hospitalised_patients  ,wi)/10.0 ,                                                     label= 'lits occupés (hopital) (dizaines)',  color="indigo", marker=hospmarker, lw=3, ls='--')
    plt.fill_between(dep_data["date"], slid_window_avg(dep_data.n_icu_patients_public  ,wi), slid_window_avg(dep_data.n_icu_patients_icubam  ,wi), label= 'dont réa (icubam vs pub. data)', alpha=0.2, facecolor='indigo')
    # plt.plot(        dep_data["date"], slid_window_avg(dep_data.n_icu_patients_public  ,wi),                                                       label= 'dont réa (publique)',     color="indigo", marker=hospmarker, lw=3, ls='-.')
    plt.plot(        dep_data["date"], slid_window_avg(dep_data.n_icu_patients_icubam  ,wi),                                                       label= 'dont réa (icubam)',  color="indigo", marker=hospmarker, lw=3, ls=':')
    plt.plot(        dep_data["date"], slid_window_avg(dep_data["n_covid_occ"],wi),                                                                label= 'dont réa covid+ (icubam)', color="darkorange", marker=reamarker, lw=2, ls=':')

    # plt.legend(loc='best')
    plt.legend(handlelength=4)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.tight_layout()
    plt.savefig(dep+".pdf")
    plt.savefig(dep+".png")
    ## explication : ##
    # assert( (d.n_covid_occ + d.n_ncovid_occ - d.n_icu_patients_icubam).sum() == 0 )
    # d.n_icu_patients_icubam == d.n_covid_occ + d.n_ncovid_occ

  fig = plt.figure(figsize=[10,5])
  plt.title("region")
  plt.plot(dep_data["date"], slid_window_avg(flow_public_hosp_region,wi), label= 'flux entrant hopital (régional, TOTAL)',          lw=2, color="blue", marker=hospmarker)
  plt.plot(dep_data["date"], slid_window_avg(flow_covidPlus_region,wi),   label= 'flux entrant réanim. (régional, TOTAL) (icubam)', lw=2, color="red", marker=reamarker)
  plt.legend(loc='best')
  plt.savefig("region-total.pdf")
  plt.savefig("region-total.png")

  # plt.ylim([-1,650])
  plt.show()
  return fig


api_key = sys.argv[1]
d = predicu.data.load_combined_icubam_public(api_key=api_key)

plot_flow_public_hosp(d)

