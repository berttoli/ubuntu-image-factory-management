"""Guard contracts between image build scripts and GitHub Actions workflows."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class BuildWorkflowTests(unittest.TestCase):
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
