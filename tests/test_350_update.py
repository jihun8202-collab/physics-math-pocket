"""Release feed behavior: never offer an unfinished public build."""
import unittest
from unittest.mock import patch
from updater import check_for_updates, _release_from_github

def release(tag,beta,assets):
    return {'tag_name':tag,'name':tag,'prerelease':beta,'assets':assets}

def payload(version,channel,build):
    return {'name':f'PhysicsMathPocket_Update_{version}_{channel}_Build{build}.zip',
            'browser_download_url':f'https://example.invalid/{build}.zip','digest':'sha256:'+'a'*64}

class Beta350UpdateTests(unittest.TestCase):
    @patch('updater._request_json')
    def test_only_finished_payload_is_offered_and_channels_stay_separate(self,request):
        request.return_value=[release('v3.5.0_Beta_Build35002',True,[]),
            release('v3.5.0_Beta_Build35001',True,[payload('3.5.0','Beta',35001)]),
            release('v3.2.0_Stable_Build32002',False,[payload('3.2.0','Stable',32002)])]
        beta=check_for_updates('3.2.0',32002,channel='beta',repository='owner/repo',source_mode='github')
        self.assertEqual(beta.status,'update_available')
        self.assertEqual((beta.release.version,beta.release.build,beta.release.channel),('3.5.0',35001,'beta'))
        self.assertEqual(beta.release.asset_kind,'package')
        self.assertEqual(beta.release.sha256,'a'*64)
        stable=check_for_updates('3.2.0',32002,channel='stable',repository='owner/repo',source_mode='github')
        self.assertEqual(stable.status,'current')
        self.assertEqual(stable.release.version,'3.2.0')

    @patch('updater._request_json',return_value=[release('v3.5.0_Beta_Build35001',True,[])])
    def test_unfinished_build_is_not_installable(self,request):
        result=check_for_updates('3.2.0',32002,channel='beta',repository='owner/repo',source_mode='github')
        self.assertEqual(result.status,'no_release')
        self.assertIsNone(result.release)
