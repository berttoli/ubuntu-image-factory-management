variable "release" {
  type    = string
  default = "26.04"
}

variable "architecture" {
  type    = string
  default = "amd64"
}

variable "iso_url" {
  type = string
}

variable "iso_checksum" {
  type = string
}

variable "output_directory" {
  type    = string
  default = "../build/vm"
}

variable "desired_format" {
  type    = string
  default = "qcow2"
}

variable "profile" {
  type    = string
  default = "hardened"
}

variable "accelerator" {
  type    = string
  default = "none"
}

variable "ssh_private_key_file" {
  type = string
}

locals {
  seed_dir = "${path.root}/../build/autoinstall/${var.release}-${var.architecture}"
  name     = "ubuntu-${var.release}-${var.architecture}-${var.desired_format}"
}

source "qemu" "ubuntu" {
  accelerator      = var.accelerator
  boot_wait        = "5s"
  cpus             = 2
  disk_compression = true
  disk_size        = "12G"
  format           = "qcow2"
  headless         = true
  http_directory   = local.seed_dir
  iso_checksum     = var.iso_checksum
  iso_url          = var.iso_url
  memory           = 2048
  net_device       = "virtio-net"
  output_directory = "${var.output_directory}/${local.name}"
  qemu_binary      = var.architecture == "arm64" ? "qemu-system-aarch64" : "qemu-system-x86_64"
  qemuargs = var.architecture == "arm64" ? [
    ["-machine", "virt"],
    ["-cpu", "max"],
    ["-bios", "/usr/share/AAVMF/AAVMF_CODE.fd"],
  ] : [
    ["-machine", "q35"],
  ]
  shutdown_command = "sudo shutdown -P now"
  ssh_private_key_file = var.ssh_private_key_file
  ssh_timeout      = "30m"
  ssh_username     = "factory"
  vm_name          = local.name
  disk_interface   = "virtio"

  boot_command = [
    "<wait5s>",
    "c<wait>",
    "linux /casper/vmlinuz autoinstall ds=nocloud-net\\;s=http://{{ .HTTPIP }}:{{ .HTTPPort }}/<enter>",
    "initrd /casper/initrd<enter>",
    "boot<enter>",
  ]
}

build {
  name    = "ubuntu-${var.release}-${var.architecture}"
  sources = ["source.qemu.ubuntu"]

  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates unattended-upgrades ufw apparmor auditd qemu-guest-agent",
      "sudo cloud-init clean --logs --seed",
      "sudo rm -f /etc/ssh/ssh_host_*",
      "sudo truncate -s 0 /etc/machine-id",
      "sudo rm -f /var/lib/dbus/machine-id",
      "sudo apt-get clean",
    ]
  }

  provisioner "shell" {
    script = "${path.root}/../ansible/scripts/apply-hardening.sh"
    execute_command = "sudo -E bash '{{ .Path }}'"
  }
}
