import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from pearl_ops.address import validate_prl_address
from pearl_ops.dashboard import _runtime_hours


ROOT = Path(__file__).resolve().parents[1]
# Native v1 encoding of an all-zero test payload; never a payout destination.
VECTOR = "prl1p" + "q" * 52 + "en4g90"


class Validation(unittest.TestCase):
    def test_checksum(self):
        validate_prl_address(VECTOR)
        for invalid in ("", "prl1p...", VECTOR[:-1] + "q", VECTOR.upper()):
            with self.assertRaises(ValueError):
                validate_prl_address(invalid)

    def test_elapsed(self):
        self.assertEqual(_runtime_hours(" 123 1-02:30:00 wildrig-multi"), 26.5)
        self.assertEqual(_runtime_hours(" 123 06:00 wildrig-multi"), 0.1)
        self.assertIsNone(_runtime_hours(""))


@unittest.skipUnless(os.name == "posix", "WSL/Linux runner")
class BoundedTrial(unittest.TestCase):
    def test_managed_lifecycle_without_gpu_or_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("scripts/trial-pearlhash.sh", "src/pearl_ops/address.py",
                         "pearlhash/stop-pearlhash-miner.sh"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / name, root / name)
            bin_dir = root / "downloads/wildrig-0.52.3"
            bin_dir.mkdir(parents=True)
            fake = bin_dir / "wildrig-multi"
            fake.write_text("#!/bin/sh\necho READY\nexec sleep 30\n")
            fake.chmod(0o755)
            # Isolate the fixture from any actual miners on the test host.
            probe = bin_dir / "pgrep"
            probe.write_text("#!/bin/sh\nexit 1\n")
            probe.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir) + ":" + os.environ["PATH"])
            (root / ".env").write_text(f"PEARL_ADDRESS={VECTOR}\nPEARLHASH_URL=unused.invalid:9000\n")
            cmd = ["bash", "scripts/trial-pearlhash.sh", "3", "managed"]
            with subprocess.Popen(cmd, cwd=root, env=env) as running:
                log = root / "pearlhash/pearlhash-miner.log"
                for _ in range(80):
                    if log.exists() and "READY" in log.read_text():
                        break
                    time.sleep(.025)
                self.assertIn("READY", log.read_text())
                duplicate = subprocess.run(cmd, cwd=root, env=env, capture_output=True)
                self.assertEqual(duplicate.returncode, 3)
                self.assertEqual(running.wait(timeout=6), 124)
            pidfile = root / "pearlhash/pearlhash-miner.pid"
            pidfile.write_text(str(os.getpid()))
            subprocess.run(["bash", "pearlhash/stop-pearlhash-miner.sh"], cwd=root, check=True)
            self.assertFalse(pidfile.exists())
