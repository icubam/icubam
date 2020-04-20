# ICU Bed Availability Monitor (ICUBAM) :bed: :hospital:

![docker build & test](https://github.com/icubam/icubam/workflows/docker%20build%20&%20test/badge.svg)
[![codecov](https://codecov.io/gh/icubam/icubam/branch/master/graph/badge.svg)](https://codecov.io/gh/icubam/icubam)

## Short description

### English

ICUBAM's goal is to provide real-time information on intensive care unit (ICU)
bed availability in French hospitals. Data is directly obtained from doctors
working inside ICU by sending them SMS with a HTTP link to a form that they can
fill in 15 seconds.

### Français

ICUBAM a pour objectif de fournir des informations en temps réel sur la
disponibilité des lits dans les unités de soin intensif (USI) des hôpitaux
français. Les données sont obtenues directement des médecins qui travaillent
dans les USI en leur envoyant des SMS avec un lien HTTP vers un formulaire
qu'ils peuvent remplir en 15 secondes, montre en main.

![map](https://icubam.github.io/assets/images/map.jpg)
![steps](https://icubam.github.io/assets/images/workflow_icubam.png)
## More information about ICUBAM

This software stack is currently being used by the ICU system in Eastern France
to help manage the COVID crisis.

The project was co-built by ICU Doctors from CHRU Nancy/Université de
Loraine and engineers from INRIA & Polytechnique. It was fleshed out live
during the Covid crisis in Eastern France to answer an urgent need for finding
available ICU beds in a saturated and deteriorating situation. At the time of
writing, 5 engineers are working full-time, 7 days a week, on the project, in
direct contact with the team of ICU doctors on the ground.

Most of the data handled by ICUBAM is less than 1 hour old. ICUBAM integrates
with the ministry of health (only ARS Est for now)'s back-end system for
- sending data upstream to inform authorities,
- and retrieving data to synchronise with other data sources.

This software is open-source and made available on
[GitHUb](https://github.com/icubam/icubam).

It will soon be released as a one-click deployable docker container.

You can contact the team for deployment information or general experience
sharing at contact@icubam.net.

This project is a collaboration between INRIA, Polytechnique, CHRU Nancy, Université de Lorraine & individual contributors.
