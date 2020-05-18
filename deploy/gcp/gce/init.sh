#!/bin/bash

# Description:
#   Performs the one-time configuration/bootstrapping required to manage
#   a deployment to GCE through Terraform.
#
# Dependencies:
#   - gcloud (https://cloud.google.com/sdk/install)
#   - terraform (https://www.terraform.io/downloads.html)
#
# Optional input environment variables:
#   - GCP_PROJECT_ID: GCP project's unique ID.
#   - GCP_SA_NAME: GCP service account name.
#   - GOOGLE_CLOUD_KEYFILE_JSON: path to GCP service account JSON keyfile, used by Terraform.

set -e


GCP_PROJECT_ID="${GCP_PROJECT_ID:-}"
GCP_SA_NAME="${GCP_SA_NAME:-}"

GCP_ROLE="${GCP_ROLE:-compute.admin}"
GOOGLE_CLOUD_KEYFILE_JSON="${GOOGLE_CLOUD_KEYFILE_JSON:-"${HOME}/.gcp/icubam.json"}"


function check_cmd_exists() {
  local cmd="${1}"
  command -v "${cmd}" >/dev/null 2>&1 || {
    echo >&2 "ERROR: ${cmd} is required but could not be found in \$PATH."
    return 1
  }
}

function check_envvar_exists() {
  local envvar="${1}"
  [ -n "${!envvar}" ] || {
    echo >&2 "WARNING: ${envvar} is not set."
  }
}

function check_dependencies() {
  local status=0
  for cmd in gcloud terraform ; do
    if ! check_cmd_exists "${cmd}" ; then
      status=1
    fi
  done
  for envvar in GCP_PROJECT_ID GCP_SA_NAME GOOGLE_CLOUD_KEYFILE_JSON ; do
    check_envvar_exists "${envvar}"
  done
  return "${status}"
}

function print_envvar_instructions() {
  local envvar="${1}"
  echo >&2 "Going forward, please ensure the following environment variable is exported:"
  echo >&2 "\$ export ${envvar}=\"${!envvar}\""
}

function choose_gcp_project() {
  gcloud projects list
  read -r -p "Enter project ID: " GCP_PROJECT_ID
  export GCP_PROJECT_ID
  print_envvar_instructions "GCP_PROJECT_ID"
}

function create_gcp_service_account() {
  read -r -p "Enter service account username: " GCP_SA_NAME
  export GCP_SA_NAME
  print_envvar_instructions "GCP_SA_NAME"

  # Create a new service account, with least privilege, to use with Terraform:
  gcloud iam service-accounts create "${GCP_SA_NAME}" \
    --description "${GCP_SA_NAME}'s service account to automatically deploy to GCP via Terraform" \
    --display-name "${GCP_SA_NAME}"

  # Grant required permissions to the created service account:
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member "serviceAccount:${GCP_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role "roles/${GCP_ROLE}"
}

function create_gcp_key_file() {
  # Create a JSON key on your machine, to be provided to Terraform later on:
  mkdir -p "$(dirname "${GOOGLE_CLOUD_KEYFILE_JSON}")"
  gcloud iam service-accounts keys create "${GOOGLE_CLOUD_KEYFILE_JSON}" \
    --iam-account "${GCP_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  export GOOGLE_CLOUD_KEYFILE_JSON
  print_envvar_instructions "GOOGLE_CLOUD_KEYFILE_JSON"
}

function init_gcp() {
  gcloud version
  gcloud auth login
  [ -z "${GCP_PROJECT_ID}" ] && choose_gcp_project
  gcloud config set project "${GCP_PROJECT_ID}"
  [ -z "${GCP_SA_NAME}" ] && create_gcp_service_account
  [ ! -f "${GOOGLE_CLOUD_KEYFILE_JSON}" ] && create_gcp_key_file
}

function init_terraform() {
  terraform version
  terraform init
  terraform plan
}

function main() {
  check_dependencies
  init_gcp
  init_terraform
}

main
