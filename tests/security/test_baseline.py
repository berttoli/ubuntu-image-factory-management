import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = (ROOT / "configs/security/baseline.yaml").read_text()

    def test_ssh_disables_root_and_password_login(self):
        self.assertIn('PermitRootLogin: "no"', self.policy)
        self.assertIn('PasswordAuthentication: "no"', self.policy)

    def test_container_exception_does_not_enable_ssh_or_systemd(self):
        self.assertIn("systemd: false", self.policy)
        self.assertIn("sshd: false", self.policy)
        self.assertIn("user: factory", self.policy)

    def test_rules_have_rationale_and_validation(self):
        self.assertNotIn("rationale: TODO", self.policy)
        self.assertNotIn("validation: TODO", self.policy)


if __name__ == "__main__":
    unittest.main()

