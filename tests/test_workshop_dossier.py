import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
from tools.build_workshop_dossier import build, verify

CODE=b'G21G90G54\nM06T1\nG43H1\nM03S18000\nG0X0Y0Z27\nG1Z0F3000\nG1X10F10000\nM05\nM100\nM30\n'
PROFILE={'tools':[{'tool_number':1,'diameter_mm':6}],'production_z_zero_reference':'machine_table_surface'}


class DossierTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/'nc';self.source.mkdir()
        self.file=self.source/'sample.nc';self.file.write_bytes(CODE)
        self.output=self.root/'dossier'

    def test_dossier_roundtrip_and_source_unchanged(self):
        report=build(self.source,PROFILE,self.output)
        self.assertEqual(self.file.read_bytes(),CODE)
        self.assertTrue(verify(self.source,self.output,PROFILE)['file_evidence_current'])
        self.assertFalse(report['machine_release_allowed'])
        self.assertEqual(len(list(self.output.glob('*.nc'))),0)
        self.assertEqual((self.output/'index.html').read_text(encoding='utf-8').count('<svg '),3)
        with (self.output/'feed_runs.csv').open(encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['tool'],'1')

    def test_no_overwrite_or_output_in_input(self):
        build(self.source,PROFILE,self.output)
        before=(self.output/'dossier.json').read_bytes()
        with self.assertRaises(FileExistsError):build(self.source,PROFILE,self.output)
        self.assertEqual((self.output/'dossier.json').read_bytes(),before)
        with self.assertRaises(ValueError):build(self.source,PROFILE,self.source/'reports')

    def test_detect_nc_report_and_configuration_changes(self):
        build(self.source,PROFILE,self.output)
        self.file.write_bytes(CODE+b';changed\n')
        self.assertFalse(verify(self.source,self.output,PROFILE)['file_evidence_current'])
        self.file.write_bytes(CODE)
        changed=copy.deepcopy(PROFILE);changed['tools'][0]['diameter_mm']=5
        self.assertFalse(verify(self.source,self.output,changed)['file_evidence_current'])
        (self.output/'index.html').write_text('replaced',encoding='utf-8')
        self.assertFalse(verify(self.source,self.output,PROFILE)['file_evidence_current'])

    def test_detect_new_and_removed_programs(self):
        build(self.source,PROFILE,self.output)
        (self.source/'extra.nc').write_bytes(CODE)
        self.assertTrue(any(p['reason']=='new_nc_file' for p in verify(self.source,self.output,PROFILE)['problems']))
        self.file.unlink()
        self.assertTrue(any(p.get('file')=='sample.nc' for p in verify(self.source,self.output,PROFILE)['problems']))

    def test_invalid_trace_does_not_get_feed_counts(self):
        self.file.write_bytes(b'G90\nG2X1Y1I1J1\nM30')
        report=build(self.source,PROFILE,self.output)
        self.assertEqual(report['programs'][0]['feed_inventory']['runs'],[])
        self.assertFalse(report['programs'][0]['review']['trace_complete'])

    def test_manifest_path_escape_rejected(self):
        build(self.source,PROFILE,self.output)
        path=self.output/'manifest.json'
        data=json.loads(path.read_text())
        data['sources']['../outside.nc']='fake'
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):verify(self.source,self.output,PROFILE)

    def test_csv_filename_not_interpreted_as_formula(self):
        self.file.rename(self.source/'=sample.nc')
        build(self.source,PROFILE,self.output)
        with (self.output/'feed_runs.csv').open(encoding='utf-8-sig') as f:
            row=next(csv.DictReader(f))
        self.assertTrue(row['file'].startswith("'="))
