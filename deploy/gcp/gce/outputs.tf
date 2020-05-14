output "public_ips" {
  value = ["${google_compute_instance.vm_instance.*.network_interface.0.access_config.0.nat_ip}"]
}

output "private_ips" {
  value = ["${google_compute_instance.vm_instance.*.network_interface.0.network_ip}"]
}
