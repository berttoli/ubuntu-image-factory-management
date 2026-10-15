import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class FactoryTests(unittest.TestCase):
    def test_supported_release_tracks_are_present(self):
        text = (ROOT / "configs/factory.yaml").read_text()
        self.assertIn('default_release: "26.04"', text)
        self.assertIn('"26.04":', text)
        self.assertIn('"24.04":', text)

    def test_artifact_name_is_immutable_and_traceable(self):
        pattern = re.compile(r"^ubuntu-\d{2}\.04-(amd64|arm64)-(baremetal|qcow2|raw|oci)-\d{4}\.\d{2}\.\d{2}$")
        for name in ("ubuntu-26.04-amd64-qcow2-2026.10.15", "ubuntu-24.04-arm64-oci-2026.10.15"):
            self.assertRegex(name, pattern)

    def test_schema_is_valid_json(self):
        schema = json.loads((ROOT / "schemas/factory.schema.json").read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)


if __name__ == "__main__":
    unittest.main()

