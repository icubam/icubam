provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
  version = "~> 3.18"
}

resource "google_compute_address" "static" {
  name = "${var.project_name}-ipv4-address"
}

resource "google_compute_instance" "vm_instance" {
  name         = "${var.project_name}-instance"
  machine_type = var.gcp_machine_type

  boot_disk {
    initialize_params {
      image = var.gcp_os_image
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.static.address
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_username}:${file(var.ssh_public_key_path)}"
  }
}
