# Modules
import argparse
from datetime import datetime
import time
import unittest

# Import raspberry-sprinkles Modules
import rsapi
import rsclient as rsc

class TestRSAPI(unittest.TestCase):
  current_result = None

  def run(self, result=None):
    self.current_result = result
    unittest.TestCase.run(self, result)

  @classmethod
  def setup_class(cls):
    # Unit Testing Mode ON
    rsc.unit_testing(parsed_args.url, 1, parsed_args.schedule)

  @classmethod
  def tear_down_class(cls):
    # Unit Testing Mode OFF
    rsc.unit_testing(parsed_args.url, 0, parsed_args.schedule)

  def setup(self):
    self.assert_equal(rsc.resetAllData(parsed_args.url).status_code, 204)

  def tear_down(self):
    ok = self.current_result.wasSuccessful()
    global final_result
    if not ok:
      final_result = False

  def test_custom_gpio_mapping(self):
    self.assert_equal(rsapi.gpio_mapping(8, 1), 5)
    self.assert_equal(rsapi.gpio_mapping(3, 1), 26)

  def test_get_sprinkler_id(self):
    self.assert_equal(rsc.get_sprinkler_id(parsed_args.url), 1)

  def test_sprinkler_builder(self):
    # Test get/update/delete w/ no sprinklers
    self.assert_equal(rsc.get_sprinkler(parsed_args.url, 1).status_code, 404)
    self.assert_equal(rsc.update_sprinkler(parsed_args.url, 1, 'sprinkler1', 10).status_code, 404)
    self.assert_equal(rsc.delete_sprinkler(parsed_args.url, 1).status_code, 404)
    self.assert_equal(rsc.get_all_sprinklers(parsed_args.url).status_code, 404)

    # Test adding sprinklers
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler1', 10).status_code, 201)
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler2', 20).status_code, 201)
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler3', 30).status_code, 201)
    self.assert_equal(rsc.get_sprinkler_id(parsed_args.url), 4)
    self.assert_equal(rsc.get_all_sprinklers(parsed_args.url).status_code, 200)

    # Test get/update/delete w/ sprinklers
    self.assert_equal(rsc.get_sprinkler(parsed_args.url, 1).status_code, 200)
    self.assert_equal(rsc.update_sprinkler(parsed_args.url, 1, 'sprinkler1', 11).status_code, 201)
    self.assert_equal(rsc.update_sprinkler(parsed_args.url, 1, 'sprinklerone', 11).status_code, 201)
    self.assert_equal(rsc.update_sprinkler(parsed_args.url, 1, 'sprinklerone1', 111).status_code, 201)
    self.assert_equal(rsc.update_sprinkler(parsed_args.url, 1, 'sprinklerone1', 111).status_code, 400)
    self.assert_equal(rsc.delete_sprinkler(parsed_args.url, 1).status_code, 204)
    self.assert_equal(rsc.delete_sprinkler(parsed_args.url, 2).status_code, 204)
    self.assert_equal(rsc.delete_sprinkler(parsed_args.url, 3).status_code, 204)
    self.assert_equal(rsc.get_sprinkler_id(parsed_args.url), 1)
    self.assert_equal(rsc.get_all_sprinklers(parsed_args.url).status_code, 404)

  def test_schedule_builder(self):
    weekend = ['Sun', 'Sat']

    # Test add/update/delete w/ no sprinklers
    self.assert_equal(rsc.add_schedule(parsed_args.url, 1, 'Mon', '05:00', 1).status_code, 404)
    self.assert_equal(rsc.get_schedule(parsed_args.url, 1).status_code, 404)
    self.assert_equal(rsc.update_schedule(parsed_args.url, 1, 'Thu', '05:00', 1).status_code, 404)
    self.assert_equal(rsc.delete_schedule(parsed_args.url, 1).status_code, 404)
    self.assert_equal(rsc.get_all_schedules(parsed_args.url).status_code, 404)

    # Test get/update/delete w/ no schedules w/ sprinklers
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler1', 10).status_code, 201)
    self.assert_equal(rsc.get_schedule(parsed_args.url, 1).status_code, 404)
    self.assert_equal(rsc.update_schedule(parsed_args.url, 1, 'Mon', '05:00', 5).status_code, 404)
    self.assert_equal(rsc.delete_schedule(parsed_args.url, 1).status_code, 404)
    self.assert_equal(rsc.get_all_schedules(parsed_args.url).status_code, 404)

    # Test adding schedules w/ sprinklers
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler2', 20).status_code, 201)
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler3', 30).status_code, 201)
    self.assert_equal(rsc.add_schedule(parsed_args.url, 1, 'Mon', '05:00', 1).status_code, 201)
    self.assert_equal(rsc.add_schedule(parsed_args.url, 2, 'Tue', '06:00', 2).status_code, 201)
    self.assert_equal(rsc.add_schedule(parsed_args.url, 3, 'Wed', '07:00', 3).status_code, 201)
    self.assert_equal(rsc.add_schedule(parsed_args.url, 3, ['Mon','Tue'], '11:00', 1), None)
    self.assert_equal(rsc.get_schedule(parsed_args.url, 1).status_code, 200)
    self.assert_equal(rsc.get_schedule_id(parsed_args.url), 6)
    self.assert_equal(rsc.get_all_schedules(parsed_args.url).status_code, 200)

    # Test get/update/delete w/ schedules
    self.assert_equal(rsc.get_schedule(parsed_args.url, 1).status_code, 200)
    self.assert_equal(rsc.update_schedule(parsed_args.url, 1, 'Thu', '05:00', 1).status_code, 201)
    self.assert_equal(rsc.update_schedule(parsed_args.url, 2, 'Tue', '06:01', 2).status_code, 201)
    self.assert_equal(rsc.update_schedule(parsed_args.url, 3, 'Wed', '07:00', 4).status_code, 201)
    self.assert_equal(rsc.update_schedule(parsed_args.url, 3, 'Sun', '12:00', 10).status_code, 201)
    self.assert_equal(rsc.update_schedule(parsed_args.url, 3, weekend, '11:00', 10), None)
    self.assert_equal(rsc.delete_schedule(parsed_args.url, 1).status_code, 204)
    self.assert_equal(rsc.delete_schedule(parsed_args.url, 2).status_code, 204)
    self.assert_equal(rsc.delete_schedule(parsed_args.url, 3).status_code, 204)
    self.assert_equal(rsc.delete_schedule(parsed_args.url, 4).status_code, 204)
    self.assert_equal(rsc.delete_schedule(parsed_args.url, 5).status_code, 204)
    self.assert_equal(rsc.get_schedule_id(parsed_args.url), 1)
    self.assert_equal(rsc.get_all_schedules(parsed_args.url).status_code, 404)

    # Test delete sprinkler to remove schedules
    self.assert_equal(rsc.add_schedule(parsed_args.url, 1, 'Mon', '05:00', 1).status_code, 201)
    self.assert_equal(rsc.delete_sprinkler(parsed_args.url, 1).status_code, 204)
    self.assert_equal(rsc.get_schedule(parsed_args.url, 1).status_code, 404)

  def test_rain_delay(self):
    # Test get/patch/delete raindelay
    self.assert_equal(rsc.get_rain_delay(parsed_args.url).status_code, 200)
    self.assert_equal(rsc.patch_rain_delay(parsed_args.url).status_code, 201)
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler1', 10).status_code, 201)
    self.assert_equal(rsc.add_schedule(parsed_args.url, 1, datetime.now().strftime("%a"), datetime.now().strftime("%H:%M"), 1).status_code, 201)
    self.assert_equal(rsc.run_schedule(parsed_args.url, 1).status_code, 202)
    self.assert_equal(rsc.delete_rain_delay(parsed_args.url).status_code, 204)

  def test_run_adhoc(self):
    # Test with no sprinklers
    self.assert_equal(rsc.run_adhoc(parsed_args.url, 1, 5).status_code, 404)

    # Test with sprinkler
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler1', 10).status_code, 201)
    self.assert_equal(rsc.run_adhoc(parsed_args.url, 1, 1).status_code, 200)
    time.sleep(2)

    # Test stopping sprinkler
    self.assert_equal(rsc.run_adhoc(parsed_args.url, 1, 5).status_code, 200)
    self.assert_equal(rsc.stop_running(parsed_args.url).status_code, 200)
    time.sleep(2)

  def test_run_schedule(self):
    # Test with no schedule
    self.assert_equal(rsc.run_schedule(parsed_args.url, 1).status_code, 404)

    # Test with schedule
    self.assert_equal(rsc.add_sprinkler(parsed_args.url, 'sprinkler1', 10).status_code, 201)
    self.assert_equal(rsc.add_schedule(parsed_args.url, 1, 'Mon', '05:00', 1).status_code, 201)
    self.assert_equal(rsc.run_schedule(parsed_args.url, 1).status_code, 200)
    time.sleep(2)

if __name__ == '__main__':
  arg_parser = argparse.ArgumentParser(description="Raspberry Sprinkles Unit Testing")
  arg_parser.add_argument("-s", "--schedule", help="schedule file", default='unit_testing_schedule.json')
  arg_parser.add_argument("-u", "--url", help="base url", default='')
  parsed_args = arg_parser.parse_args()
  final_result = True
  unittest.main(exit=True)
  print(final_result)