"""Guard contracts between image build scripts and GitHub Actions workflows."""

from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class BuildWorkflowTests(unittest.TestCase):
    def test_container_matrix_builds_the_requested_platform(self) -> None:
        workflow = json.loads(subprocess.check_output(
            ["ruby", "-rjson", "-ryaml", "-e", "puts JSON.generate(YAML.load_file(ARGV[0]))",
             str(ROOT / ".github/workflows/build-container.yml")],
            text=True,
        ))
        job = workflow["jobs"]["build"]
        architecture_check = next(
            step["run"] for step in job["steps"] if "docker image inspect" in step.get("run", "")
        )
        with tempfile.TemporaryDirectory() as directory:
            tools = Path(directory)
            docker = tools / "docker"
            docker.write_text(
                '#!/bin/sh\n'
                'if [ "$1" = buildx ]; then printf "%s\\n" "$@" > "$DOCKER_ARGS"; fi\n'
                'if [ "$1" = image ]; then printf "%s\\n" "$DOCKER_IMAGE_ARCH"; fi\n',
                encoding="utf-8",
            )
            docker.chmod(0o755)
            for arch in job["strategy"]["matrix"]["arch"]:
                with self.subTest(arch=arch):
                    env = os.environ.copy()
                    env.pop("ARCH", None)
                    env.update({
                        "PATH": f"{tools}{os.pathsep}{env['PATH']}",
                        "DOCKER_ARGS": str(tools / "docker-args"),
                        "PUBLISH": "0",
                        "IMAGE_NAME": f"factory-test:26.04-{arch}",
                    })
                    if "ARCH" in job["env"]:
                        env["ARCH"] = job["env"]["ARCH"].replace("${{ matrix.arch }}", arch)
                    subprocess.run(
                        ["make", "build-container", "RELEASE=26.04"],
                        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
                    )
                    arguments = (tools / "docker-args").read_text(encoding="utf-8").splitlines()
                    self.assertEqual(arguments[arguments.index("--platform") + 1], f"linux/{arch}")
                    self.assertEqual(arguments[arguments.index("--tag") + 1], env["IMAGE_NAME"])
                    self.assertIn("--load", arguments)
                    self.assertNotIn("--push", arguments)
                    for actual_arch in (arch, "unexpected"):
                        env["DOCKER_IMAGE_ARCH"] = actual_arch
                        result = subprocess.run(
                            ["bash", "-e", "-c", architecture_check],
                            cwd=ROOT, env=env, capture_output=True, text=True,
                        )
                        self.assertEqual(result.returncode, 0 if actual_arch == arch else 1, result.stderr)

    def test_vm_boot_test_uses_generated_artifact_name(self) -> None:
        script = (ROOT / "scripts/build/build-vm.sh").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/build-vm.yml").read_text(encoding="utf-8")
        self.assertIn('target_image="$output_dir/ubuntu-${release}-${arch}.${format}"', script)
        self.assertIn('packer_output_dir="$output_dir/ubuntu-${release}-${arch}-${format}"', script)
        self.assertIn('find "$packer_output_dir" -maxdepth 1', script)
        self.assertNotIn('find "$output_dir" -type f', script)
        self.assertIn('IMAGE="build/vm/ubuntu-${RELEASE}-${ARCH}.qcow2"', workflow)

    def test_installer_media_workflow_checks_required_inputs(self) -> None:
        workflow = (ROOT / ".github/workflows/build-baremetal.yml").read_text(encoding="utf-8")
        self.assertIn("Check required installer inputs", workflow)
        self.assertIn('-z "$AUTOINSTALL_SSH_PUBLIC_KEY"', workflow)

    def test_vm_workflow_uses_throwaway_credentials_not_secrets(self) -> None:
        workflow = (ROOT / ".github/workflows/build-vm.yml").read_text(encoding="utf-8")
        self.assertIn('AUTOINSTALL_EPHEMERAL_CREDENTIALS: "1"', workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertIn("Acceptance test", workflow)

    def test_throwaway_credentials_are_sealed_out_of_the_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = subprocess.check_output(
                [str(ROOT / "scripts/build/ephemeral-credentials.sh"), directory], text=True,
            )
            self.assertIn("export AUTOINSTALL_SEAL_CREDENTIALS=1", output)
            self.assertIn("export AUTOINSTALL_PASSWORD_HASH='$6$", output)
            key = Path(directory) / "factory-build-ed25519"
            self.assertEqual(key.stat().st_mode & 0o077, 0)
            self.assertNotIn(key.read_text(encoding="utf-8").splitlines()[1], output)
        packer = (ROOT / "packer/ubuntu.pkr.hcl").read_text(encoding="utf-8")
        for removed in ("/etc/sudoers.d/90-factory-build", "/home/factory/.ssh/authorized_keys", "passwd -l factory"):
            self.assertIn(removed, packer)
        self.assertIn("shutdown_command = local.shutdown", packer)

    def test_only_vm_builds_may_skip_the_disk_serial(self) -> None:
        def render(extra):
            with tempfile.TemporaryDirectory() as directory:
                env = {
                    "PATH": os.environ["PATH"],
                    "AUTOINSTALL_PASSWORD_HASH": "$6$example$examplehash",
                    "AUTOINSTALL_SSH_PUBLIC_KEY": "ssh-ed25519 AAAAexample test",
                    **extra,
                }
                result = subprocess.run(
                    ["python3", str(ROOT / "scripts/autoinstall/render.py"), "--release", "26.04",
                     "--arch", "amd64", "--profile", "hardened", "--output", directory],
                    env=env, capture_output=True, text=True,
                )
                seed = Path(directory) / "user-data"
                return result.returncode, seed.read_text(encoding="utf-8") if seed.exists() else ""

        code, _ = render({})
        self.assertNotEqual(code, 0, "installer media must not render without a disk serial")
        code, seed = render({"AUTOINSTALL_TARGET_DISK_SERIAL": "SERIAL123"})
        self.assertEqual(code, 0)
        self.assertIn("serial: 'SERIAL123'", seed)
        self.assertNotIn("NOPASSWD", seed)
        self.assertNotIn("__", seed)
        code, seed = render({"AUTOINSTALL_STORAGE_MATCH": "single-disk", "AUTOINSTALL_BUILD_SUDO": "1"})
        self.assertEqual(code, 0)
        self.assertIn("size: largest", seed)
        self.assertNotIn("serial:", seed)
        self.assertIn("/etc/sudoers.d/90-factory-build", seed)
        iso_builder = (ROOT / "scripts/build/build-iso.sh").read_text(encoding="utf-8")
        self.assertNotIn("AUTOINSTALL_STORAGE_MATCH", iso_builder)
        self.assertNotIn("AUTOINSTALL_BUILD_SUDO", iso_builder)

    def test_security_monitor_requests_vm_rebuilds_without_secrets(self) -> None:
        workflow = (ROOT / ".github/workflows/security-monitor.yml").read_text(encoding="utf-8")
        self.assertIn("gh workflow run build-vm.yml", workflow)
        self.assertNotIn("secrets.AUTOINSTALL", workflow)

    def test_vm_image_is_trimmed_and_compressed(self) -> None:
        packer = (ROOT / "packer/ubuntu.pkr.hcl").read_text(encoding="utf-8")
        self.assertIn('disk_discard       = "unmap"', packer)
        self.assertIn('disk_detect_zeroes = "unmap"', packer)
        self.assertIn("fstrim", (ROOT / "scripts/build/prepare-template.sh").read_text(encoding="utf-8"))
        self.assertIn("qemu-img convert -c -O qcow2", (ROOT / "scripts/build/build-vm.sh").read_text(encoding="utf-8"))

    def test_image_validation_installs_and_scopes_prerequisites(self) -> None:
        workflow = (ROOT / ".github/workflows/test-images.yml").read_text(encoding="utf-8")
        self.assertIn("sudo apt-get install -y qemu-system-x86 qemu-system-arm qemu-utils", workflow)
        self.assertIn("github.event.workflow_run.name == 'build-vm'", workflow)
        self.assertIn("github.event.workflow_run.name == 'build-baremetal'", workflow)
        self.assertIn("github.event.workflow_run.name == 'build-container'", workflow)
        self.assertIn("command -v docker", workflow)
        self.assertIn("command -v qemu-system-x86_64", workflow)


if __name__ == "__main__":
    unittest.main()
