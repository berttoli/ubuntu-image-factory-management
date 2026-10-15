# Upstream assessment

Reviewed 2026-10-15. These projects were evaluated as references, not copied dependencies.

| Project | Finding | Decision |
| --- | --- | --- |
| [jjbailey/ubuntu-autoinstall](https://github.com/jjbailey/ubuntu-autoinstall) | Active small MIT-licensed ISO/USB/cidata builder. Its README documents a bootstrap password example and a destructive USB write workflow. | Reuse the general autoinstall/media concept only. This factory requires runtime credentials and an inventory-reviewed disk serial. |
| [jcksnvllxr80/ubuntu-from-scratch](https://github.com/jcksnvllxr80/ubuntu-from-scratch) | Small public reference with autoinstall and debootstrap approaches for Ubuntu 26.04; useful comparison of ISO and raw-rootfs tradeoffs. | Do not vendor. The factory separates Packer/QEMU, autoinstall, and OCI paths and keeps upstream code attribution out of the implementation. |
| [canonical/imagecraft](https://github.com/canonical/imagecraft) | Canonical GPL-3.0 bootable-image tool with active development and craft-library dependencies. | Optional future bootable-image backend; not required for the Packer/QEMU or server-ISO paths. |
| [canonical/ubuntu-image](https://github.com/canonical/ubuntu-image) | Canonical GPL-3.0 official image tool focused on snap-based and classical image definitions; requires elevated permissions. | Not used as the generic VM builder; retain as an evaluated option for Ubuntu Core/classical image extensions. |
| [actions/runner-images](https://github.com/actions/runner-images) | GitHub runner image definitions currently expose Ubuntu 26.04 x64/Arm64 and Ubuntu 24.04 labels; runner contents are intentionally broad and include third-party tools. | Use GitHub-hosted Ubuntu 24.04 for conservative CI, pin a specific label rather than `ubuntu-latest`, and install only the build tools required by each workflow. |

Canonical Ubuntu release metadata is consumed from the official release/checksum locations. 26.04.1 is the primary point release and 24.04.5 is the compatibility point release recorded in `configs/factory.yaml`; arm64 server ISOs use the Canonical cdimage path.

