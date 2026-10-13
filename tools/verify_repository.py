"""A release must use the actual registered repository without bundled credentials."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--repository", required=True)
args = parser.parse_args()
configuration = json.loads((Path(__file__).resolve().parents[1] / "data/update_config.json").read_text(encoding="utf-8-sig"))
configured = configuration.get("github_repository", configuration.get("repository", ""))
if configured != args.repository or "/" not in configured:
    raise SystemExit("Update configuration must match the actual registered GitHub repository.")
if any(word in key.lower() for key in configuration for word in ("token", "password", "secret")):
    raise SystemExit("Credentials must not be included in update configuration.")
print("Confirmed actual update repository: " + configured)
