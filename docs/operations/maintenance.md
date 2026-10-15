# Maintenance and recovery

Image maintenance produces newly patched artifacts. Host maintenance keeps deployed systems patched through unattended security updates, reboot scheduling, and package/update logs. Container maintenance rebuilds and redeploys images when base-image or dependency vulnerabilities are detected.

If SSH access is lost, use the provider/console recovery path, inspect `journalctl -u ssh`, validate `/etc/ssh/sshd_config`, and temporarily restore access through an approved console-only change. Do not re-enable password SSH globally.

For rollback, retain the prior stable image and release manifest, stop the affected workload, restore the prior artifact or VM snapshot, and record the incident. A newly published image does not alter running hosts or containers.

