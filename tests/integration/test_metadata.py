import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class MetadataTests(unittest.TestCase):
    def test_metadata_records_sha256(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            artifact = directory / "sample.raw"
            artifact.write_bytes(b"factory")
            metadata = directory / "metadata.json"
            subprocess.run(
                ["python3", str(ROOT / "scripts/release/generate-metadata.py"), "--artifact", str(artifact), "--release", "26.04", "--architecture", "amd64", "--type", "raw", "--output", str(metadata)],
                check=True,
            )
            data = json.loads(metadata.read_text())
            self.assertEqual(data["sha256"], hashlib.sha256(b"factory").hexdigest())
            self.assertEqual(data["artifact_type"], "raw")


if __name__ == "__main__":
    unittest.main()

