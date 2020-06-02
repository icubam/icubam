# Release notes

## v0.5.2

 - Added a standalone analytics service which
   - periodically re-generates plots for the dashboard
   - exposes the import/export endpoints
   without blocking the main server (#407)
 - Added sphinx documentation available at
   [docs.icubam.net](https://docs.icubam.net) (#417)
 -  Add `--create-admin` option to `scripts/update_password.py` (#409) 

## v0.5.1

 - Use docker hub (#406)
 - Add Docker user envvar (#400)
 - Add Terraform template to create VM under GCP (#398)
 - Update nginx configurations to handle proxy with no ssl endpoint (#414)
 - Add disclaimer link on maps (#397) 
 - Faster ``/version`` endpoint (#411) 
 - Fix bug in ``plot_each_region`` (#413) 


