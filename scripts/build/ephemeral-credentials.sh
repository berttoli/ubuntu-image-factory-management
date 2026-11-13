#!/usr/bin/env bash
# Generate throwaway build credentials for one VM build and print them as shell exports.
#
#   eval "$(scripts/build/ephemeral-credentials.sh <private-directory>)"
#
# The key pair and password hash exist only so Packer can reach the machine it is
# installing. AUTOINSTALL_SEAL_CREDENTIALS=1 tells the build to remove the key, lock the
# password and drop build-time sudo before the image is captured, so the finished image
# contains no login credential at all; access is supplied at deployment through
# cloud-init. The password itself is random and is never written anywhere.
set -Eeuo pipefail

dir="${1:?usage: ephemeral-credentials.sh <private-directory>}"
[[ -d "$dir" ]] || { echo "ERROR: directory not found: $dir" >&2; exit 2; }
command -v ssh-keygen >/dev/null 2>&1 || { echo "ERROR: ssh-keygen is required" >&2; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "ERROR: openssl is required" >&2; exit 1; }

chmod 0700 "$dir"
key="$dir/factory-build-ed25519"
rm -f "$key" "$key.pub"
ssh-keygen -q -t ed25519 -N '' -C factory-build-ephemeral -f "$key"
hash="$(openssl rand -base64 48 | openssl passwd -6 -stdin)"
[[ "$hash" =~ ^\$6\$[./A-Za-z0-9]+\$[./A-Za-z0-9]+$ ]] || { echo "ERROR: unexpected password hash format" >&2; exit 1; }

printf "export AUTOINSTALL_PASSWORD_HASH='%s'\n" "$hash"
printf "export AUTOINSTALL_SSH_PUBLIC_KEY='%s'\n" "$(cat "$key.pub")"
printf "export AUTOINSTALL_SSH_PRIVATE_KEY_FILE='%s'\n" "$key"
printf "export AUTOINSTALL_SEAL_CREDENTIALS=1\n"
