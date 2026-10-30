# Maintenance and recovery

Image maintenance produces newly patched artifacts. Host maintenance keeps deployed systems patched through unattended security updates, reboot scheduling, and package/update logs. Container maintenance rebuilds and redeploys images when base-image or dependency vulnerabilities are detected.

If SSH access is lost, use the provider/console recovery path, inspect `journalctl -u ssh`, validate `/etc/ssh/sshd_config`, and temporarily restore access through an approved console-only change. Do not re-enable password SSH globally.

For rollback, retain the prior stable image and release manifest, stop the affected workload, restore the prior artifact or VM snapshot, and record the incident. A newly published image does not alter running hosts or containers.

The daily upstream and security monitors create or refresh a single open issue per topic. Their bodies include current ISO checksums or OVAL feed digests and the monitor run link; reviewer notes remain intact. A cache miss may be the monitor's first observation rather than a regression. To refresh existing [metadata](https://github.com/berttoli/ubuntu-image-factory-management/issues/6) or [security feed](https://github.com/berttoli/ubuntu-image-factory-management/issues/7) evidence without dispatching unchanged candidate builds, manually run the corresponding monitor workflow with `refresh_issue=true`. Review the upstream point releases and builder dependencies for the metadata issue. For the security issue, inspect candidate build and scanner results and record promotion or remediation evidence before closure. A changed feed digest alone is not a vulnerability finding.

When an unseen security feed digest is found, the monitor requests container candidate builds. It requests VM candidate builds only when all three required Autoinstall repository secrets are present; otherwise the security issue records the missing prerequisite. Scheduled `build-vm` and `build-baremetal` workflows still fail at their own credential checks until those secrets are configured. Once configured, manually run `build-vm` for both supported releases and review their boot/security evidence.
