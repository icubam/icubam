# ICU Bed Activity Monitor (ICUBAM) :bed: :hospital:

## Short description

### English

ICUBAM's goal is to provide real-time information on intensive care unit (ICU)
bed availability in French hospitals. Data is directly obtained from doctors
working inside ICU by sending them SMS with a http link to a form that they can
fill in 15 seconds.

### French

ICUBAM a pour objectif the fournir des informations en temps réel sur la
disponibilité des lits dans les unités de soin intensif (USI) des hôpitaux
français. Les données sont obtenues directemnt des médecins qui travaillent
dans les USI en leur envoyant des SMS avec un lien http vers un formulaire
qu'ils peuvent remplire en 15 secondes, montre en main.

![map](/images/map.jpg)

## More information about ICUBAM

This software is currently running live.  It collects data sent by 97 doctors
in 41 ICU wards in the Easter France region.

The project started on March 28th. The initial idea was provided by an ICU
doctor, Dr. Kimounn. It fleshed out live during the Covid crisis in Eastern
France. It answers an urgent need for finding available ICU beds in a saturated
and deteriorating situation. At the time of writing, 5 engineers are working
full-time, 7 days a week, on the project.

Most of the data handled by ICUBAM is less than 1 hour old. ICUBAM integrates
with the ministry of health's backend for
- sending data upstream to inform authorities,
- and retrieving data to synchronise with other data sources.

This software is open-source and made available on
[GitHUb](https://github.com/icubam/icubam).

It will soon be released as a one-click deployable docker container.
