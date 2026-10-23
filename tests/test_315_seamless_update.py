import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from core import APP_BUILD, APP_CHANNEL, APP_VERSION
from updater import _release_from_github
from update_agent import apply_update

class SeamlessUpdateTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(APP_VERSION, "3.5.10"); self.assertEqual(APP_BUILD, 35100); self.assertEqual(APP_CHANNEL, "beta")
    def test_github_prefers_zip_package(self):
        item={"tag_name":"v3.1.8-beta-build31801","prerelease":True,"assets":[{"name":"PhysicsMathPocket_Setup_3.1.8_Beta_Build31801.exe","browser_download_url":"https://example.invalid/setup.exe","digest":"sha256:"+"a"*64},{"name":"PhysicsMathPocket_Update_3.1.8_Beta_Build31801.zip","browser_download_url":"https://example.invalid/update.zip","digest":"sha256:"+"b"*64}]}
        rel=_release_from_github(item,"PhysicsMathPocket_Setup"); self.assertEqual(rel.asset_kind,"package"); self.assertTrue(rel.asset_name.endswith(".zip"))
    def test_agent_applies_verified_package(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); install=base/'app'; install.mkdir(); (install/'PhysicsMathPocket.exe').write_bytes(b'old')
            payload=b'new-version'; digest=hashlib.sha256(payload).hexdigest(); package=base/'update.zip'
            manifest={"version":"3.1.8","build":31801,"files":[{"path":"PhysicsMathPocket.exe","sha256":digest,"size":len(payload)}]}
            with zipfile.ZipFile(package,'w') as z: z.writestr('update-manifest.json',json.dumps(manifest)); z.writestr('payload/PhysicsMathPocket.exe',payload)
            version,build=apply_update(package,install); self.assertEqual((version,build),("3.1.8",31801)); self.assertEqual((install/'PhysicsMathPocket.exe').read_bytes(),payload); self.assertTrue((install/'.pmp-files.json').exists())
    def test_repo_has_release_workflow(self):
        text=(Path(__file__).resolve().parents[1]/'.github/workflows/release.yml').read_text(encoding='utf-8'); self.assertIn('build_release.py',text); self.assertIn('gh release create $env:RELEASE_TAG',text); self.assertIn('--prerelease',text)

if __name__ == '__main__': unittest.main()



