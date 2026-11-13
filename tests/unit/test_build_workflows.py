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

    def test_credential_gated_workflows_check_required_inputs(self) -> None:
        for workflow_name, required in (
            ("build-vm.yml", "AUTOINSTALL_SSH_PRIVATE_KEY"),
            ("build-baremetal.yml", "AUTOINSTALL_SSH_PUBLIC_KEY"),
        ):
            with self.subTest(workflow=workflow_name):
                workflow = (ROOT / ".github/workflows" / workflow_name).read_text(encoding="utf-8")
                self.assertIn("Check required installer inputs" if workflow_name == "build-baremetal.yml" else "Materialize ephemeral SSH key file", workflow)
                self.assertIn(f'-z "${required}"', workflow)

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
