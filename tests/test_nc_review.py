import unittest
from core.nc_review import review_nc


class NCReviewTests(unittest.TestCase):
    def run_code(self, text):
        return review_nc(text, {1:6, 3:15, 4:5}, z_zero='machine_table_surface')

    def test_modal_axes_and_feed(self):
        report=self.run_code('G90 G54\nM06 T1\nG43 H1\nM03 S18000\nG0X0Y0Z27\nG1Z0F3000\nX10F10000\nY20\nM05\nM100\nM30')
        self.assertTrue(report['trace_complete'])
        self.assertEqual(report['segments'][-1]['to'], dict(X=10,Y=20,Z=0))
        self.assertEqual(report['segments'][-1]['feed'],10000)
        self.assertFalse(report['manufacturing_approved'])
        self.assertFalse(report['custom_commands'][0]['meaning_verified'])

    def test_unsupported_motion_invalidates_following_trace(self):
        report=self.run_code('G90\nG0X0Y0Z27\nG91\nG1X5F100\nM30')
        self.assertFalse(report['trace_complete'])
        self.assertEqual(len(report['segments']),1)

    def test_rejects_unknown_tool_and_offset(self):
        report=self.run_code('G90\nM06T8\nG43H1\nM03S100\nG1X0Y0Z0F10\nM30')
        self.assertGreaterEqual(len(report['issues']),2)

    def test_negative_z_and_missing_footer(self):
        report=self.run_code('G90\nG0X0Y0Z-1')
        self.assertFalse(report['trace_complete'])
        self.assertTrue(any('below' in i['message'] for i in report['issues']))

    def test_unparsed_and_duplicate_words(self):
        for text in ['G90\nG0X1X2Y0Z0\nM30', 'G90\nG2X2Y2I1J1\nM30', 'BAD\nM30']:
            with self.subTest(text=text):
                self.assertFalse(self.run_code(text)['trace_complete'])

    def test_unparsed_motion_does_not_propagate_fake_path(self):
        report=self.run_code('G90G54\nG0X0Y0Z27\nG2X10Y0I5J0\nG1X20F100\nM30')
        self.assertEqual(len(report['segments']),1)

    def test_tool_preselection_does_not_change_loaded_tool(self):
        report=self.run_code('G90G54\nM06T1\nG43H1\nM03S18000\nG0X0Y0Z27\nT3\nG1X10F100\nM05\nM30')
        self.assertTrue(report['trace_complete'])
        self.assertEqual(report['segments'][-1]['tool'],1)

    def test_tool_change_requires_new_offset(self):
        report=self.run_code('G90G54\nM06T1\nG43H1\nG0X0Y0Z27\nM06T1\nM03S18000\nG1Z0F100\nM30')
        self.assertTrue(any('offset' in i['message'] for i in report['issues']))

    def test_offset_value_without_g43_is_not_applied(self):
        report=self.run_code('G90G54\nM06T1\nH1\nM03S18000\nG0X0Y0Z27\nG1Z0F100\nM30')
        self.assertFalse(report['trace_complete'])

    def test_program_end_does_not_trace_following_lines(self):
        report=self.run_code('G90G54\nG0X0Y0Z27\nM30\nG0X50')
        self.assertEqual(len(report['segments']),1)
        self.assertFalse(report['trace_complete'])

    def test_explicit_units_and_conflicting_modes(self):
        self.assertEqual(self.run_code('G21G90G54\nG0X0Y0Z27\nM30')['units_evidence'],'explicit_G21')
        self.assertFalse(self.run_code('G90G54\nG0G1X0Y0Z27\nM30')['trace_complete'])


if __name__=='__main__':
    unittest.main()
