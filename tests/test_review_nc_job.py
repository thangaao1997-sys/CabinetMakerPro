import tempfile
import unittest
from pathlib import Path
from tools.review_nc_job import review_folder


class ReviewFolderTests(unittest.TestCase):
    def test_nested_files_and_case_insensitive_extension(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'sheet').mkdir()
            first=root/'sheet'/'a.NC'
            first.write_bytes(b'G90G54\nG0X0Y0Z27\nM30\n')
            before=first.read_bytes()
            (root/'ignored.txt').write_text('unrelated')
            result=review_folder(root,{'tools':[]})
            self.assertEqual(result['files_reviewed'],1)
            self.assertEqual(result['programs'][0]['source_relative_path'],'sheet/a.NC')
            self.assertEqual(first.read_bytes(),before)
            self.assertFalse(result['machine_release_allowed'])

    def test_empty_folder_is_not_a_successful_job(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):review_folder(folder,{'tools':[]})
