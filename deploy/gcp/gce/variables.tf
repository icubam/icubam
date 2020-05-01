variable "gcp_project_id" {
  description = "Google Cloud Platform selected project's ID"
}

variable "ssh_username" {
  description = "User to configure SSH access for"
}

variable "ssh_public_key_path" {
  description = "Path to file containing public key"
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_private_key_path" {
  description = "Path to file containing private key"
  default     = "~/.ssh/id_rsa"
}

variable "project_name" {
  description = "Project name, used to name VMs and other resources"
  default     = "icubam"
}

variable "gcp_region" {
  # See also:
  # - https://cloud.google.com/compute/docs/regions-zones
  # - $ gcloud compute regions list
  description = "Google Cloud Platform's selected region"
  default     = "europe-west1"
}

variable "gcp_zone" {
  # See also:
  # - https://cloud.google.com/compute/docs/regions-zones
  # - $ gcloud compute zones list
  description = "Google Cloud Platform's selected zone"
  default     = "europe-west1-b"
}

variable "gcp_machine_type" {
  # See also:
  # - https://cloud.google.com/compute/docs/machine-types
  # - $ gcloud compute machine-types list
  description = "Google Cloud Platform's selected machine type"
  default     = "g1-small"
}

variable "gcp_os_image" {
  # See also:
  # - https://cloud.google.com/compute/docs/images
  # - $ gcloud compute images list
  description = "Google Cloud Platform OS"
  default     = "ubuntu-os-cloud/ubuntu-minimal-2004-lts"
  # default     = "cos-cloud/cos-stable"  # May be useful to have a more locked-down environment, just to run Docker images.
}
