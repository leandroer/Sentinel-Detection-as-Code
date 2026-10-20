import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('release_name',Path(__file__).resolve().parents[1]/'scripts/release_name.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
class ReleaseNameTests(unittest.TestCase):
    def test_supported_version(self):
        self.assertEqual(module.archive_name('v1.2.3-rc.1'),'sentinel-detection-as-code-v1.2.3-rc.1.tar.gz')
    def test_shell_metacharacters_and_paths_rejected(self):
        for tag in ['v$(id)','v1.2.3;id','v1.2.3`id`','v1.2.3/../../x','v1.2.3\nother']:
            with self.subTest(tag=tag),self.assertRaises(ValueError):module.archive_name(tag)
if __name__=='__main__':unittest.main()
