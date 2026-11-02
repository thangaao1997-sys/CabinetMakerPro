import unittest
from core.nc_review import review_nc
from core.feed_inventory import inventory_feed_runs

HEADER='G21G90G54\nM06T1\nG43H1\nM03S18000\nG0X0Y0Z10\n'


class FeedInventoryTests(unittest.TestCase):
    def inventory(self,code):
        return inventory_feed_runs(review_nc(HEADER+code+'\nM05\nM30',{1:6}))

    def test_vertical_moves_are_not_assumed_holes(self):
        result=self.inventory('G1Z0F100\nG0Z10\nG0X20\nG1Z2F100')
        self.assertEqual(len(result['runs']),2)
        self.assertEqual(result['runs'][0]['classification'],'z_only_feed_run')
        self.assertIsNone(result['runs'][0]['machining_feature_identity'])
        self.assertIsNone(result['runs'][0]['cut_depth_mm'])
        self.assertAlmostEqual(result['total_feed_distance_mm'],18)

    def test_closed_contour_and_ideal_time(self):
        result=self.inventory('G1Z0F100\nG1X10F100\nY10\nX0\nY0')
        run=result['runs'][0]
        self.assertTrue(run['closed_in_xy'])
        self.assertEqual(run['classification'],'xyz_feed_run')
        self.assertAlmostEqual(run['feed_distance_mm'],50)
        self.assertAlmostEqual(run['ideal_feed_travel_minutes'],.5)

    def test_unsupported_input_cannot_get_partial_success(self):
        result=self.inventory('G1Z0F100\nG2X10Y0I5J0')
        self.assertEqual(result['status'],'blocked_trace_incomplete')
        self.assertEqual(result['runs'],[])
        self.assertIsNone(result['total_feed_distance_mm'])

    def test_nonmotion_gap_splits_runs_conservatively(self):
        result=self.inventory('G1X10F100\nS16000\nG1X20')
        self.assertEqual(len(result['runs']),2)

    def test_zero_xy_distance_is_not_closed_contour(self):
        self.assertFalse(self.inventory('G1Z0F100')['runs'][0]['closed_in_xy'])

    def test_diagonal_length_uses_three_dimensions(self):
        run=self.inventory('G1X3Y4Z10F100')['runs'][0]
        self.assertAlmostEqual(run['feed_distance_mm'],5)
