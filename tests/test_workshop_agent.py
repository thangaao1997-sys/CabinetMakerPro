import copy
import json
from pathlib import Path
import unittest
from core.workshop_agent import prepare_job


class WorkshopAgentTests(unittest.TestCase):
    def setUp(self):
        self.scene = json.loads((Path(__file__).resolve().parents[1] / 'examples/scene.json').read_text())

    def test_sample_inventory_and_no_invented_machining(self):
        before = copy.deepcopy(self.scene)
        job = prepare_job(self.scene)
        self.assertEqual(job['panel_count'], 5)
        self.assertEqual(job['panels'][0]['finished_face_candidate_mm'], [553, 720])
        self.assertEqual(job['panels'][-1]['thickness_candidate_mm'], 7)
        self.assertTrue(all(p['blank_size_mm'] is None for p in job['panels']))
        self.assertFalse(job['manufacturing_approved'])
        self.assertFalse(job['cnc_files_generated'])
        self.assertEqual(before, self.scene)

    def test_changed_source_invalidates_job_fingerprint(self):
        before = prepare_job(self.scene)['source_scene_sha256']
        self.scene['objects'][0]['size_mm']['y'] = 552
        self.assertNotEqual(before, prepare_job(self.scene)['source_scene_sha256'])

    def test_missing_or_bad_inputs_rejected(self):
        mutations = [lambda s: s.update(units='in'),
                     lambda s: s.update(manufacturing_approved=True),
                     lambda s: s['objects'][0]['size_mm'].update(x=True),
                     lambda s: s['objects'][0]['origin_mm'].update(x=9999),
                     lambda s: s['objects'].append(copy.deepcopy(s['objects'][0]))]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                scene = copy.deepcopy(self.scene)
                mutate(scene)
                with self.assertRaises(ValueError):
                    prepare_job(scene)

    def test_intersections_rejected(self):
        self.scene['objects'][1]['origin_mm']['x'] = 1
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            prepare_job(self.scene)

    def test_ambiguous_thickness_requires_review(self):
        self.scene['objects'] = [dict(id='CUBE', material='panel',
            origin_mm=dict(x=0,y=0,z=0), size_mm=dict(x=17,y=17,z=17))]
        panel = prepare_job(self.scene)['panels'][0]
        self.assertIsNone(panel['thickness_axis_candidate'])
        self.assertIsNone(panel['finished_face_candidate_mm'])


if __name__ == '__main__':
    unittest.main()
