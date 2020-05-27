.. icubam documentation master file, created by
   sphinx-quickstart on Fri May 22 15:46:05 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ICUBAM documentation
====================

Short description
-----------------
ICUBAM's goal is to provide real-time information on intensive care unit (ICU)
bed availability in French hospitals. Data is directly obtained from doctors
working inside ICU by sending them SMS with a HTTP link to a form that they can
fill in 15 seconds.

Detailed description
--------------------

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
`Github <https://github.com/icubam/icubam>`_.

It will soon be released as a one-click deployable docker container.

You can contact the team for deployment information or general experience
sharing at contact@icubam.net.

This project is a collaboration between INRIA, Polytechnique, CHRU Nancy, Université de Lorraine & individual contributors.

.. toctree::
   :maxdepth: 1
   :caption: Usage

   install.md
   docker.md



.. toctree::
   :maxdepth: 1
   :caption: Technical documentation

   authentication.md
   backoffice.md
   cli.md


.. toctree::
   :maxdepth: 1
   :caption: ICUBAM project

   contributing.md
   whats_new.md
