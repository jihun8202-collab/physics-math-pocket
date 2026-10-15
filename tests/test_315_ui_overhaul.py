import unittest
from pathlib import Path
from core import APP_VERSION, APP_BUILD, APP_CHANNEL

ROOT=Path(__file__).resolve().parents[1]

class UIOverhaul315Tests(unittest.TestCase):
    def test_revision_identity(self):
        self.assertEqual(APP_VERSION,'3.5.0')
        self.assertEqual(APP_BUILD,35001)
        self.assertEqual(APP_CHANNEL,'beta')

    def test_new_shell_components_exist(self):
        source=(ROOT/'app.py').read_text(encoding='utf-8')
        for marker in ['self.nav_rail','self.main_stack','빠른 탐색','업데이트 센터','apply_windows_chrome','hero_a','hero_b']:
            self.assertIn(marker,source)

    def test_legacy_permanent_sidebars_removed(self):
        source=(ROOT/'app.py').read_text(encoding='utf-8')
        self.assertIn('legacy permanent category sidebar was removed',source)
        self.assertIn('legacy permanent right sidebar was removed',source)

    def test_new_brand_assets_exist(self):
        for name in ['physics_pocket.ico','physics_pocket.png','physics_pocket_512.png','wizard.bmp','wizard_small.bmp']:
            path=ROOT/'assets'/name
            self.assertTrue(path.exists(),name)
            self.assertGreater(path.stat().st_size,100,name)

    def test_installer_build_is_revision_build(self):
        text=(ROOT/'installer.iss').read_text(encoding='utf-8')
        self.assertIn('PhysicsMathPocket_Setup_{#MyAppVersion}_{#MyAppChannel}_Build{#MyAppBuild}',text)

if __name__=='__main__':
    unittest.main()



