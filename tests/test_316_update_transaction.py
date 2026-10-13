import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import update_agent


class UpdateTransactionTests(unittest.TestCase):
    def make_package(self, root, files, corrupt=False):
        package = root / 'next.zip'
        entries = [{'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}
                   for name, data in files.items()]
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('update-manifest.json', json.dumps({'version': '3.1.7', 'build': 31700, 'files': entries}))
            for name, data in files.items():
                archive.writestr('payload/' + name, data + (b'corrupt' if corrupt else b''))
        return package

    def test_bad_hash_does_not_change_install_or_user_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = root / 'app'
            install.mkdir()
            (install / 'PhysicsMathPocket.exe').write_bytes(b'old')
            (install / 'personal-note.txt').write_bytes(b'keep')
            package = self.make_package(root, {'PhysicsMathPocket.exe': b'new'}, corrupt=True)
            with self.assertRaises(ValueError):
                update_agent.apply_update(package, install)
            self.assertEqual((install / 'PhysicsMathPocket.exe').read_bytes(), b'old')
            self.assertEqual((install / 'personal-note.txt').read_bytes(), b'keep')

    def test_interrupted_update_restores_removed_and_replaced_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = root / 'app'
            install.mkdir()
            original = {'PhysicsMathPocket.exe': b'old', 'retired.dll': b'old-runtime'}
            for name, data in original.items():
                (install / name).write_bytes(data)
            metadata = json.dumps({'files': list(original)}).encode()
            (install / '.pmp-files.json').write_bytes(metadata)
            package = self.make_package(root, {'PhysicsMathPocket.exe': b'new', 'fresh.dll': b'fresh'})
            replace = update_agent.os.replace
            def fail_second(source, destination):
                if Path(destination).name == 'fresh.dll':
                    raise OSError('Simulated locked file')
                return replace(source, destination)
            with patch('update_agent.os.replace', side_effect=fail_second):
                with self.assertRaises(OSError):
                    update_agent.apply_update(package, install)
            for name, data in original.items():
                self.assertEqual((install / name).read_bytes(), data)
            self.assertEqual((install / '.pmp-files.json').read_bytes(), metadata)
            self.assertFalse((install / 'fresh.dll').exists())
            self.assertFalse(list(install.glob('*.pmp-new')))

    def test_manifest_paths_cannot_escape_installation(self):
        for path in ['../outside', 'C:/outside', '/outside', 'sub/../outside', 'file:stream', 'name.']:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    update_agent.safe_relative(path)

    def test_user_data_survives_successful_update(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = root / 'app'
            user = root / 'PhysicsMathPocket'
            user.mkdir()
            for name, data in {'favorites.json': b'{"values":["old-term"]}', 'term_notes.json': b'{"old-term":"note"}', 'knowledge_user.db': b'user-database'}.items():
                (user / name).write_bytes(data)
            before = {p.name: p.read_bytes() for p in user.iterdir()}
            package = self.make_package(root, {'PhysicsMathPocket.exe': b'new'})
            self.assertEqual(update_agent.apply_update(package, install), ('3.1.7', 31700))
            self.assertEqual({p.name: p.read_bytes() for p in user.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
