# Google Cloud Engine

[Google Cloud Engine][gcp-gce] is a service offering VMs in Google's cloud.
In that sense, running ICUBAM on GCE is not particularly different from any
other VM.

This example shows how to deploy ICUBAM on GCE using Terraform, which brings the
benefits of Infrastructure as Code (IaC), such as:

- a human (and machine) readable description of your infrastructure,
- the ability to reliably reproduce your setup.

## Setup

### Pre-requisites

1. Create or select a project from the [GCP's projects page][gcp-projects].
2. Download & install [GCP's SDK / `gcloud`][gcp-sdk]. This will be used for
   imperative, one-time operations.
3. Download & install [Terraform][tf-dl]. This will be used to manage your
   infrastructure in a declarative way.

### Initialisation

In order to manage your infrastructure in a declarative way via Terraform, we
need to:

- create a service account,
- configure this service account with a minimum set of permissions,
- create a key so that it can securely access GCP.

If you have all this already, please ensure the following environment variable
are:

- set (replace the values with appropriate ones, where relevant),
- exported (you can use [`direnv`][direnv] for that purpose).

```console
export GOOGLE_CLOUD_KEYFILE_JSON="${HOME}/.gcp/icubam.json"
export GCP_PROJECT_ID="icubam-272015"
export GCP_SA_NAME="$(whoami)"
```

Optionally, to avoid having Terraform prompt you on every command, you can have:

```console
export TF_VAR_gcp_project_id="${GCP_PROJECT_ID}"
export TF_VAR_project_name="$(whoami)-test"
export TF_VAR_ssh_username="$(whoami)"
```

Otherwise, please run:

```console
./init.sh
```

### Terraforming

#### Create / Update

To create or update your infrastructure, run:

```console
terraform apply
```

#### Delete

To delete your infrastructure, run:

```console
terraform destroy
```

### Notes

Various [permissions][gcp-permissions] are required to create, access, update or
delete VMs and network components in GCP, e.g.:

- `compute.networks.create`
- `compute.images.get`
- `compute.instances.create`
- `compute.disks.create`
- `compute.instances.setMetadata`
- and many others.

The `compute.admin` role seem to include most of these permissions, while also
not being too permissive and therefore following the
"_Least Privilege Principle_" and is therefore what is being used by `init.sh`.
This can be overriden by setting `GCP_ROLE` to any other preferred value.

[direnv]: https://direnv.net/
[gcp-gce]: https://cloud.google.com/compute
[gcp-permissions]: https://cloud.google.com/iam/docs/permissions-reference
[gcp-projects]: https://console.cloud.google.com/project
[gcp-sa]: https://console.cloud.google.com/iam-admin/serviceaccounts
[gcp-sdk]: https://cloud.google.com/sdk/install
[tf-dl]: https://www.terraform.io/downloads.html
