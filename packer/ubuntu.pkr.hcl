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

variable "serial_log" {
  type        = string
  default     = "../build/logs/packer-serial.log"
  description = "File that receives the installer's and the installed system's serial console."
}

variable "seal_credentials" {
  type        = bool
  default     = false
  description = "Remove the build key, lock the build password and drop build-time sudo before the image is captured."
}

locals {
  seed_dir = "${path.root}/../build/autoinstall/${var.release}-${var.architecture}"
  name     = "ubuntu-${var.release}-${var.architecture}-${var.desired_format}"
  # Sealing happens in the same command that powers the machine off, because it removes
  # the access Packer is using.
  seal     = "rm -f /etc/sudoers.d/90-factory-build /home/factory/.ssh/authorized_keys; passwd -l factory >/dev/null; "
  shutdown = "sudo sh -c '${var.seal_credentials ? local.seal : ""}shutdown -P now'"
  # qemuargs replaces Packer's own -machine flag, including the accelerator it would
  # have added, so the accelerator has to be restated here.
  accel = var.accelerator == "none" ? "tcg" : var.accelerator
  cpu   = var.accelerator == "kvm" ? "host" : "max"
}

source "qemu" "ubuntu" {
  accelerator      = var.accelerator
  boot_wait        = "8s"
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
    ["-machine", "virt,accel=${local.accel}"],
    ["-cpu", "max"],
    ["-bios", "/usr/share/AAVMF/AAVMF_CODE.fd"],
    ["-serial", "file:${var.serial_log}"],
  ] : [
    ["-machine", "q35,accel=${local.accel}"],
    ["-cpu", local.cpu],
    ["-serial", "file:${var.serial_log}"],
  ]
  shutdown_command = local.shutdown
  ssh_private_key_file = var.ssh_private_key_file
  ssh_timeout      = "45m"
  # Packer also reaches the live installer's SSH server, which rejects the build user
  # until the installed system boots. Those rejections must not end the build.
  ssh_handshake_attempts = 1000
  ssh_username     = "factory"
  vm_name          = local.name
  disk_interface   = "virtio"

  boot_command = [
    "c<wait3s>",
    "linux /casper/vmlinuz autoinstall console=tty0 console=ttyS0,115200n8 ds=nocloud-net\\;s=http://{{ .HTTPIP }}:{{ .HTTPPort }}/<enter>",
    "initrd /casper/initrd<enter><wait>",
    "boot<enter>",
  ]
}

build {
  name    = "ubuntu-${var.release}-${var.architecture}"
  sources = ["source.qemu.ubuntu"]

  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates unattended-upgrades ufw apparmor auditd qemu-guest-agent cloud-init",
    ]
  }

  provisioner "shell" {
    script = "${path.root}/../ansible/scripts/apply-hardening.sh"
    execute_command = "sudo -E bash '{{ .Path }}'"
  }

  provisioner "shell" {
    script = "${path.root}/../scripts/build/prepare-template.sh"
    execute_command = "sudo -E bash '{{ .Path }}'"
  }
}
