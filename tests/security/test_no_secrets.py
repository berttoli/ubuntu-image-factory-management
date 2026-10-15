import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SecretTests(unittest.TestCase):
    def test_templates_use_runtime_markers(self):
        template = (ROOT / "autoinstall/templates/user-data.yaml.tmpl").read_text()
        self.assertIn("__PASSWORD_HASH__", template)
        self.assertIn("__SSH_PUBLIC_KEY__", template)
        self.assertIn("__DISK_SERIAL__", template)
        self.assertIsNone(re.search(r"BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY", template))


if __name__ == "__main__":
    unittest.main()

