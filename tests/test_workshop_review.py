import copy
import unittest
from core.workshop_review import review_job

PROGRAM = b'G90 G54\nM06 T1\nG43 H1\nM03 S18000\nG0X0Y0Z27\nG1Z0F3000\nG1X10F10000\nM05\nM100\nM30\n'


class WorkshopReviewTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'tools':[{'tool_number':1,'diameter_mm':6}],
                        'production_z_zero_reference':'machine_table_surface'}

    def test_readable_trace_is_not_release(self):
        before=copy.deepcopy(self.profile)
        report=review_job(PROGRAM,self.profile)
        self.assertTrue(report['trace_complete'])
        codes={b['code'] for b in report['release_blockers']}
        self.assertTrue({'startup_units_unknown','controller_unknown','custom_m_codes_unvalidated',
                         'head_mapping_missing','physical_tool_unverified','setup_and_simulation_pending'} <= codes)
        self.assertFalse(report['machine_release_allowed'])
        self.assertEqual(self.profile,before)
        self.assertEqual(report['tool_usage'][0]['xy_feed_values'],[10000])
        self.assertEqual(report['tool_usage'][0]['z_only_feed_values'],[3000])

    def test_explicit_units_and_source_change(self):
        old=review_job(PROGRAM,self.profile)
        changed=review_job(b'G21\n'+PROGRAM,self.profile)
        self.assertEqual(changed['units_evidence'],'explicit_G21')
        self.assertNotEqual(changed['source_nc_sha256'],old['source_nc_sha256'])
        self.assertNotIn('startup_units_unknown',{b['code'] for b in changed['release_blockers']})

    def test_reference_difference_not_safety_limit(self):
        self.profile['tools'][0]['feed_mm_min']=8000
        report=review_job(PROGRAM,self.profile)
        self.assertEqual(report['template_comparisons'][0]['program_values'],[10000])
        self.assertIn('not a proven',report['template_comparisons'][0]['meaning'])

    def test_cannot_bypass_release_with_profile_flags(self):
        self.profile.update(controller='example',m100_function='example',manufacturing_approved=True)
        self.profile['tools'][0].update(machine_head=1,physical_tool_geometry_verified='yes')
        report=review_job(PROGRAM,self.profile)
        self.assertFalse(report['machine_release_allowed'])
        self.assertIn('physical_tool_unverified',{b['code'] for b in report['release_blockers']})

    def test_invalid_diameter_and_duplicate_tools(self):
        for value in [True,0,-1,float('nan')]:
            with self.subTest(value=value):
                self.profile['tools'][0]['diameter_mm']=value
                with self.assertRaises(ValueError):review_job(PROGRAM,self.profile)
        self.profile['tools']=[{'tool_number':1,'diameter_mm':6}]*2
        with self.assertRaises(ValueError):review_job(PROGRAM,self.profile)
