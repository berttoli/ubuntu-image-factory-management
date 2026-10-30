import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class FactoryTests(unittest.TestCase):
    def test_supported_release_tracks_are_present(self):
        text = (ROOT / "configs/factory.yaml").read_text()
        self.assertIn('default_release: "26.04"', text)
        self.assertIn('"26.04":', text)
        self.assertIn('"24.04":', text)

    def test_schema_is_valid_json(self):
        schema = json.loads((ROOT / "schemas/factory.schema.json").read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)


if __name__ == "__main__":
    unittest.main()
