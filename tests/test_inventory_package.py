import tempfile
import unittest
from pathlib import Path
import zipfile
from tools.build_inventory_rbz import build_reader, MEMBERS


class InventoryPackageTests(unittest.TestCase):
    def test_reader_archive_and_source_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'reader.rbz'
            result=build_reader(path)
            self.assertEqual(result['files'],3)
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(sorted(archive.namelist()),sorted(MEMBERS))
                self.assertIsNone(archive.testzip())
                self.assertIn(b'SketchupExtension.new',archive.read('ai_idea_workshop.rb'))

    def test_repeatable_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'one.rbz'
            first=build_reader(path)
            second=build_reader(Path(folder)/'two.rbz')
            self.assertEqual(first['sha256'],second['sha256'])
            with self.assertRaises(FileExistsError):build_reader(path)

    def test_missing_sources_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):build_reader(Path(folder)/'reader.rbz',root=folder)
