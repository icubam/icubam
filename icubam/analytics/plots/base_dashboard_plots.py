import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import icubam
import icubam.predicu.data
import icubam.predicu.plot

data_source = ["bedcounts"]

# Logic of this code: the computation of quantities, even when seemingly simple,
# is performed separately from the plotting.  The computing is done once, at the
# dept level, and the function returns simple arrays, to be plotted.  These
# arrays are meant to be added, to the regional leel (hence, no eprcentage at
# this level) The computing at the regional level comes from that of the
# departmental level. Percentages have to be recomputed (not averaged, but
# averaged with ponderation, so, recomputed)


def slid_window_avg(a, wi):
  """ a simple window-averaging function, centerd on the current point """
  # TODO: replace with pandas rolling average. - rth
  acopy = np.array(a).copy()
  a_smoothed = np.zeros(acopy.shape)
  wi_half = wi // 2
  wi_other_half = wi - wi_half
  for i in range(acopy.shape[0]):
    aslice = acopy[max(0, i - wi_half):min(i + wi_other_half, acopy.shape[0])]
    a_smoothed[i] = np.mean(aslice, axis=0)
    # a_smoothed[i] += np.sum(aslice,axis=0)/ (aslice).shape[0]
    # print(aslice,a_smoothed[i] , acopy[i])
  return a_smoothed


def compute_all_for_plots_by_dept(d, bc, dep):
  '''
  where all computation takes place.
  is supposed to return stuff that make sense to add
  i.e. no percentages, only numbers (to aggregate from dept to region, we jsut
  sum numbers of dept)

  some quantities are defined, then set to zero, because at present the dat ais
  not loaded + we haven't thought about it too much but these are the kind of
  quantitites that we COULD think of plotting (are interestig for Antoine)
  '''
  dep_data = d[d["department"] == dep]
  dep_data = dep_data.sort_values(by="date")
  zeros = dep_data['n_covid_deaths'] * 0.0

  nicu_dep = bc[bc.department == dep
                ].icu_name.unique().size  ## number of ICUs in the dept.

  wi = 3  # sliding window time average

  ## flux covid (hopital, rea)
  flow_hopital_covid = slid_window_avg((
    dep_data[set([
      "n_hospitalised_patients", "n_hospital_death", "n_hospital_healed"
    ])].sum(axis=1)
  ).diff(1).fillna(0), wi)
  flow_reanima_covid = slid_window_avg((
    dep_data[set([
      'n_covid_deaths', 'n_covid_healed', 'n_covid_transfered', 'n_covid_occ'
    ])].sum(axis=1)
  ).diff(1).fillna(0), wi)
  ## des donnees sont aussi disponible depuis une autre source, SPF :
  #   Nombre de nouveaux cas : (i.e, le FLUX)
  #     Nombre quotidien de personnes nouvellement hospitalisées pour COVID-19
  #     Nombre quotidien de nouvelles admissions en réanimation pour COVID-19

  ## flux non-covid (hopital, rea)
  flow_hopital_n_cov = zeros  # est-ce estimable a partir des data SOS medecin ?
  ## donnees SOS medecin:
  # nbre_pass_corona    -> passage aux urgences liés au corona (par age)  (attention ! tout passage ne debouche pas sur une hospitalisation !)
  # nbre_pass_tot       -> passage aux urgences (total)        (par age)  (idem, attention !)
  # nbre_hospit_corona  -> envoi à l'hopital, lié au corona    (par age)  (interpretatin a verifier !!)
  flow_reanima_n_cov = zeros  # il nous manque les flux sortants (morts, rad) de la rea non-covid
  ##-> ca c'est introuvable, je pense

  wi = 3  # sliding window time average

  ## lits covid (hopital, rea)
  numberBed_hopital_covid_occup = slid_window_avg(
    dep_data.n_hospitalised_patients, wi
  )
  numberBed_reanima_covid_occup = slid_window_avg(dep_data.n_covid_occ, wi)
  numberBed_reanima_covid_total = slid_window_avg(
    (dep_data.n_covid_occ + dep_data.n_covid_free), wi
  )

  ## lits non-covid (hopital, rea)
  numberBed_hopital_n_cov_occup = zeros  # unknown
  numberBed_reanima_n_cov_occup = slid_window_avg(dep_data.n_ncovid_occ, wi)
  numberBed_reanima_n_cov_total = slid_window_avg(
    (dep_data.n_ncovid_occ + dep_data.n_ncovid_free), wi
  )

  cdep = pd.DataFrame({
    "date": dep_data.date,
    "flow_hopital_covid": flow_hopital_covid,
    "flow_reanima_covid": flow_reanima_covid,
    "numberBed_hopital_covid_occup": numberBed_hopital_covid_occup,
    "numberBed_reanima_covid_occup": numberBed_reanima_covid_occup,
    "numberBed_reanima_covid_total": numberBed_reanima_covid_total,
    "flow_hopital_n_cov": flow_hopital_n_cov,
    "flow_reanima_n_cov": flow_reanima_n_cov,
    "numberBed_hopital_n_cov_occup": numberBed_hopital_n_cov_occup,
    "numberBed_reanima_n_cov_occup": numberBed_reanima_n_cov_occup,
    "numberBed_reanima_n_cov_total": numberBed_reanima_n_cov_total,
    "nicu_dep": nicu_dep,
  })
  return cdep


def plot_one_dep(cdep, dep_name):
  ## for plotting one department... OR one region
  ## the code works exactly the same to plot a region.
  #3 so in this function, think of "dep" as a departement or a region

  flow_hopital_covid = cdep.flow_hopital_covid
  flow_reanima_covid = cdep.flow_reanima_covid
  numberBed_hopital_covid_occup = cdep.numberBed_hopital_covid_occup
  numberBed_reanima_covid_occup = cdep.numberBed_reanima_covid_occup
  numberBed_reanima_covid_total = cdep.numberBed_reanima_covid_total
  # flow_hopital_n_cov = cdep.flow_hopital_n_cov
  # flow_reanima_n_cov = cdep.flow_reanima_n_cov
  # numberBed_hopital_n_cov_occup = cdep.numberBed_hopital_n_cov_occup
  numberBed_reanima_n_cov_occup = cdep.numberBed_reanima_n_cov_occup
  numberBed_reanima_n_cov_total = cdep.numberBed_reanima_n_cov_total

  # zeros = cdep.flow_hopital_covid * 0.0
  percenBed_reanima_covid_occup = 100 * (
    numberBed_reanima_covid_occup / numberBed_reanima_covid_total
  )
  # percenBed_reanima_n_cov_occup = 100 * (
  # numberBed_reanima_n_cov_occup / numberBed_reanima_n_cov_total
  # )
  # percenBed_hopital_covid_occup = 100*zeros # dep_data.n_hospitalised_patients / unknown
  # percenBed_hopital_n_cov_occup = 100*zeros # unknown / unknown
  nicu_dep = cdep.nicu_dep.iloc[0]
  x_days = [date.strftime("%d-%m") for date in sorted(cdep.date.unique())]

  ## filter the data that is unavailable (before march 30, approximately)
  ## instead of plotting 0s  (for numberBed_reanima_n_cov_total)
  ## however, for barplots, this is not needed
  # filtre_data_disponib = np.where(cdep.date >= datetime.date(2020, 3, 30))[0] ## data available only from this date , march 30
  # filtre_data_non_dispo = np.where(cdep.date < datetime.date(2020, 3, 30))[0] ## data available only from this date , march 30

  suptitle = f"{dep_name}\nDonnées pour {nicu_dep} réanimation(s)"
  subplot_title1 = "Dynamique des flux entrants covid+"
  subplot_title2 = (
    f"Niveau de saturation des lits covid+\n{nicu_dep} réanimation(s), "
    f"représentant {numberBed_reanima_covid_total.median():.0f} lits de "
    f"réa covid+ (médiane, min={numberBed_reanima_covid_total.min():.0f}+ "
    f"max={numberBed_reanima_covid_total.max():.0f}+)"
  )
  subplot_title3 = "Évolution des lits covid-"

  hospcolor = 'blue'
  hospmarker = "+"
  reacolor = 'red'
  reamarker = "*"
  nbLitsReaColor = "brown"
  nbLitsHopitalColor = "indigo"
  x_ticks_c = x_days[::3]

  fig, axs = plt.subplots(3, 1)
  fig.suptitle(suptitle)
  fig.set_figwidth(8)
  fig.set_figheight(10.5)
  axs[0].set_title(subplot_title1)
  axs[0].set_ylabel("nombre d'admission")
  axs[0].plot(
    x_days,
    flow_hopital_covid,
    label="nombre d'admission à l'hopital pour covid+ (secteur+réa)",
    color=hospcolor,
    marker=hospmarker,
    lw=3,
    ls="-"
  )
  axs[0].plot(
    x_days,
    flow_reanima_covid,
    label="nombre d'admission en réanimation pour covid+",
    color=reacolor,
    marker=reamarker,
    lw=3,
    ls="--"
  )
  axs[0].legend(handlelength=4, loc='best')  # bbox_to_anchor=(0, 0.1 ),
  axs[0].set_xticks(x_ticks_c)
  axs[0].set_ylim(bottom=0)

  axs[1].set_title(subplot_title2)
  axs[1].set_ylabel('nombre de lits', color=nbLitsHopitalColor)
  axs[1].tick_params(axis='y', labelcolor=nbLitsHopitalColor)
  axs[1].bar(
    x_days,
    numberBed_hopital_covid_occup,
    label='nombre lits occupés hopital covid+  (secteur+réa)',
    color=nbLitsHopitalColor,
    edgecolor=nbLitsHopitalColor,
    lw=2,
    ls='-',
    alpha=0.5
  )
  ## same, in line plot:
  # axs[1].plot(x_days, numberBed_hopital_covid_occup, label= 'nombre lits occupés hopital covid+  (secteur+réa)',  color=nbLitsHopitalColor, marker=hospmarker, lw=3, ls='-')
  ## creating a second y-axis
  ax2 = axs[1].twinx()  # instantiate a second axes that shares the same x-axis
  ax2.set_ylabel(
    'pourcentage occupation', color=reacolor
  )  # we already handled the x-label with axs[1]
  ax2.tick_params(axis='y', labelcolor=reacolor)
  # ax2.plot(x_days, percenBed_hopital_covid_occup, label= '% lits occupés hopital covid+  (secteur+réa)', color=reacolor, marker=reamarker, lw=2, ls="-")
  ax2.plot(
    x_days,
    percenBed_reanima_covid_occup,
    label='% lits occupés réanimation covid+',
    color=reacolor,
    marker=reamarker,
    lw=2,
    ls="--"
  )
  h1, l1 = axs[1].get_legend_handles_labels()
  h2, l2 = ax2.get_legend_handles_labels()
  ax2.set_ylim([0, 100])
  axs[1].legend(
    h1 + h2, l1 + l2, handlelength=4, loc='lower left'
  )  ## summing the two legends, to have a single legend-box in the subplot
  axs[1].set_xticks(x_ticks_c)
  axs[1].set_ylim(bottom=0)

  fig.subplots_adjust(
    hspace=0.4
  )  ## to allow for large subplot titles, add some height-space

  return fig


def plot_bed_evolutions(ax, ):
  ax.set_title(subplot_title3)
  ax.set_ylabel('nombre de lits', color=nbLitsReaColor)
  ax.tick_params(axis='y', labelcolor=nbLitsReaColor)
  # numberBed_reanima_n_cov_total[filtre_data_non_dispo] *= 0.0
  ax.bar(
    x_days,
    numberBed_reanima_n_cov_total,
    label='nombre lits de réanimation (total) covid-',
    color=nbLitsReaColor,
    edgecolor=nbLitsReaColor,
    lw=2,
    ls='-',
    alpha=0.2
  )
  ax.bar(
    x_days,
    numberBed_reanima_n_cov_occup,
    label='nombre lits de réanimation occupés covid-',
    color=nbLitsReaColor,
    edgecolor=None,
    lw=3,
    ls='-',
    alpha=0.8
  )
  ax.legend(handlelength=4, loc='best')
  ax.set_xticks(x_ticks_c)
  ax.set_ylim(bottom=0)
  return ax


def plot_all_departments(d, bc, d_dep2reg):
  """this plots one figure per department for which we have data, of course."""
  depCodesList = list(d_dep2reg.departmentCode.unique())
  figs = {}
  for dep_code in depCodesList:
    dep_name = d_dep2reg[d_dep2reg.departmentCode == dep_code
                         ].departmentName.iloc[0]
    if dep_name in d["department"].unique():
      print("Tracé ok pour le département: ", dep_name)
      cdep = compute_all_for_plots_by_dept(d, bc, dep_name)
      figs[f'flux-lits-dept-{dep_name}'] = plot_one_dep(cdep, dep_name)
    else:
      print(
        "Désolé, mais le département : ", dep_name,
        "  n'est pas présent dans nos données."
      )
  return figs


def plot_all_regions(d, bc, d_dep2reg):
  """plots the regional total
  one plot pre region
  sometimes there are few departements for which we have dat ain that region
  this will be reflected in the number of ICUs, displayed in the title
  """
  figs = {}
  for reg_code in d_dep2reg.regionCode.dropna().unique():
    reg_name = d_dep2reg[d_dep2reg.regionCode == reg_code].regionName.iloc[0]
    dep_codes = list(
      d_dep2reg[d_dep2reg.regionCode == reg_code].departmentCode
    )  ## getting the dep_code of the departments of this region
    dep_counter = 0
    print(
      "\nAggrégation des données pour la région", reg_name,
      " , incluant les départements:"
    )
    for dep_code in dep_codes:  ## going through this region's departments
      dep_name = d_dep2reg[d_dep2reg.departmentCode == dep_code
                           ].departmentName.iloc[0]
      if dep_code in d.department_code_icubam.unique(
      ):  ## check if we have the data in the database(s)
        print(dep_name)
        cdep = compute_all_for_plots_by_dept(d, bc, dep_name)
        cdep = cdep.set_index(
          "date"
        )  ## to be able to add stuff (add all but date)
        if dep_counter == 0:
          cregion = cdep.copy()  ## initialize with the first dept.
        else:
          cregion += cdep
        dep_counter += 1
      # else: ## this makes too much printing
      #   print("Désolé, mais le département : ", dep_name, "  n'est pas présent dans nos données (icubam/bedcounts).")
    if dep_counter == 0:
      print(
        "Désolé, mais la REGION : ", reg_name,
        "  n'est pas présente (du tout) dans nos données (icubam/bedcounts)."
      )
    else:
      cregion = cregion.reset_index()
      figs[f'flux-lits-region-{reg_name}'] = plot_one_dep(cregion, reg_name)
      # cregion = cregion.rename( columns={"nicu_dep": "nicu_reg"})
    # plt.show()
  return figs


def plot_all(d, bc, d_dep2reg):
  figs_all = {}
  print("\n\nplot for all regions:\n")
  figs = plot_all_regions(d, bc, d_dep2reg)
  figs_all.update(figs)

  print("\n\nplot for all departments:\n")
  figs = plot_all_departments(d, bc, d_dep2reg)
  figs_all.update(figs)
  return figs_all


def plot():
  if "combined_bedcounts_public" in data:
    d = data["combined_bedcounts_public"]
  else:
    d = icubam.predicu.data.load_combined_bedcounts_public(
      data_source="combined_bedcounts_public",
      cached_data=None,
      api_key=api_key,
      icubam_host=icubam_host
    )
  if "bedcounts" in data:
    bc = data["bedcounts"]
  else:
    bc = icubam.predicu.data.load_if_not_cached(
      data_source="bedcounts",
      cached_data=None,
      api_key=api_key,
      icubam_host=icubam_host,
    )

  ## record  bc to a file for Francois Husson
  #  datetimestr = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M")
  #  filename = "predicu_data_clean_{}.csv".format(datetimestr)
  #  bc.to_csv(filename)

  ## load the dep/region correspondance table
  d_dep2reg = icubam.predicu.data.load_france_departments()
  ## these are the useful commands:
  # regionCodesList = list(np.array(d_dep2reg.regionCode.dropna().unique() ,dtype=int) )
  # regionCodesList = [str(regionCodesList[i]) for i in range(len(regionCodesList))]
  # regionNamesList = list(d_dep2reg.regionName.unique())[:-1] # it ends with a None, that we drop
  # depCodesList = list(d_dep2reg.departmentCode.unique())
  # depNamesList = list(d_dep2reg.departmentName.unique())[:-1] # it ends with a None, that we drop

  ## plot everything:
  figs = plot_all(d, bc, d_dep2reg)

  # TODO:
  # - écrire la doc de tout ça (dans le rapport technique, donc?), de sorte a
  #   bien expliquer exactement ce qui est affiché (source des data, mode de
  #   calcul des flux, lissages choisis, et pour les fleches, idem, mode de
  #   calcul de la tendance récente, mode de calcul de la tendance future
  #   prédite)

  # TODO: Dans un cadre séparé, par département,
  # - une flêche indiquant la tendance des derniers jours
  #   haussière/baisse/stable (des chiffres relatives à la réa, à chaque fois je
  #   pense - ça j'ai oublié de lui demander - ou alors une fleche de chaque : 1
  #   hopital, 1 réa)
  # - une flêche indiquant la tendance des prochains jours (modele predictif)
  #   -- Ce graphe étant accompagné d'un lien vers une explication bien détaillée
  #   des méthodes de calcul de ces fleches haut/bas/stable.
  # - en line plot comme fond derrière les flèches, un indicateur de fiabilité
  #   des données (encore par département), du genre nombre de saisies par ICU
  #   dans les 3 derniers jours glissants (une baisse signifie moins de data donc
  #   moins de fiabilité)
  return figs, None


if __name__ == "__main__":
  api_key = sys.argv[1]
  plot(api_key=api_key)
