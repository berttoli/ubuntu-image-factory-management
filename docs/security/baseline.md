# Security baseline

The baseline is in `configs/security/baseline.yaml`. Each rule includes applicability, rationale, and a validation reference. The shell application used during image construction is `ansible/scripts/apply-hardening.sh`; the Ansible role provides an idempotent post-install path.

Host controls include key-only SSH, disabled root login, disabled password and keyboard-interactive authentication, reduced SSH retries, default-deny inbound firewall with explicit SSH, AppArmor/auditd, unattended security updates, and kernel information-disclosure/core-dump controls.

The default reboot policy is false. Operations must schedule reboots after kernel/libc updates and verify service health. No rule claims CIS certification; production owners must map exceptions to their own control framework.

Critical vulnerabilities with available fixes block promotion. High findings block promotion unless an owner records an expiring exception and a remediation issue. Tool/feed failures block promotion as well.

