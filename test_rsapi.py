# Modules
import argparse
from datetime import datetime
import time
import unittest

# Custom Modules
import rsapi
import rsclient

class TestRSAPI(unittest.TestCase):
  currentResult = None

  def run(self, result=None):
    self.currentResult = result
    unittest.TestCase.run(self, result)

  @classmethod
  def setUpClass(cls):
    # Unit Testing Mode ON
    rsclient.unitTesting(parsedArgs.url, 1, parsedArgs.schedule)

  @classmethod
  def tearDownClass(cls):
    # Unit Testing Mode OFF
    rsclient.unitTesting(parsedArgs.url, 0, parsedArgs.schedule)

  def setUp(self):
    self.assertEqual(rsclient.resetAllData(parsedArgs.url).status_code, 204)

  def tearDown(self):
    ok = self.currentResult.wasSuccessful()
    global finalResult
    if not ok:
      finalResult = False

  def test_customGPIOMapping(self):
    self.assertEqual(rsapi.customGPIOMapping(8, 1), 5)
    self.assertEqual(rsapi.customGPIOMapping(3, 1), 26)

  def test_getSprinklerID(self):
    self.assertEqual(rsclient.getSprinklerID(parsedArgs.url), 1)

  def test_SprinklerBuilder(self):
    # Test get/update/delete w/ no sprinklers
    self.assertEqual(rsclient.getSprinkler(parsedArgs.url, 1).status_code, 404)
    self.assertEqual(rsclient.updateSprinkler(parsedArgs.url, 1, 'sprinkler1', 10).status_code, 404)
    self.assertEqual(rsclient.deleteSprinkler(parsedArgs.url, 1).status_code, 404)
    self.assertEqual(rsclient.getAllSprinklers(parsedArgs.url).status_code, 404)

    # Test adding sprinklers
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler1', 10).status_code, 201)
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler2', 20).status_code, 201)
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler3', 30).status_code, 201)
    self.assertEqual(rsclient.getSprinklerID(parsedArgs.url), 4)
    self.assertEqual(rsclient.getAllSprinklers(parsedArgs.url).status_code, 200)

    # Test get/update/delete w/ sprinklers
    self.assertEqual(rsclient.getSprinkler(parsedArgs.url, 1).status_code, 200)
    self.assertEqual(rsclient.updateSprinkler(parsedArgs.url, 1, 'sprinkler1', 11).status_code, 201)
    self.assertEqual(rsclient.updateSprinkler(parsedArgs.url, 1, 'sprinklerone', 11).status_code, 201)
    self.assertEqual(rsclient.updateSprinkler(parsedArgs.url, 1, 'sprinklerone1', 111).status_code, 201)
    self.assertEqual(rsclient.updateSprinkler(parsedArgs.url, 1, 'sprinklerone1', 111).status_code, 400)
    self.assertEqual(rsclient.deleteSprinkler(parsedArgs.url, 1).status_code, 204)
    self.assertEqual(rsclient.deleteSprinkler(parsedArgs.url, 2).status_code, 204)
    self.assertEqual(rsclient.deleteSprinkler(parsedArgs.url, 3).status_code, 204)
    self.assertEqual(rsclient.getSprinklerID(parsedArgs.url), 1)
    self.assertEqual(rsclient.getAllSprinklers(parsedArgs.url).status_code, 404)

  def test_ScheduleBuilder(self):
    weekend = ['Sun', 'Sat']

    # Test add/update/delete w/ no sprinklers
    self.assertEqual(rsclient.addSchedule(parsedArgs.url, 1, 'Mon', '05:00', 1).status_code, 404)
    self.assertEqual(rsclient.getSchedule(parsedArgs.url, 1).status_code, 404)
    self.assertEqual(rsclient.updateSchedule(parsedArgs.url, 1, 'Thu', '05:00', 1).status_code, 404)
    self.assertEqual(rsclient.deleteSchedule(parsedArgs.url, 1).status_code, 404)
    self.assertEqual(rsclient.getAllSchedules(parsedArgs.url).status_code, 404)

    # Test get/update/delete w/ no schedules w/ sprinklers
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler1', 10).status_code, 201)
    self.assertEqual(rsclient.getSchedule(parsedArgs.url, 1).status_code, 404)
    self.assertEqual(rsclient.updateSchedule(parsedArgs.url, 1, 'Mon', '05:00', 5).status_code, 404)
    self.assertEqual(rsclient.deleteSchedule(parsedArgs.url, 1).status_code, 404)
    self.assertEqual(rsclient.getAllSchedules(parsedArgs.url).status_code, 404)

    # Test adding schedules w/ sprinklers
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler2', 20).status_code, 201)
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler3', 30).status_code, 201)
    self.assertEqual(rsclient.addSchedule(parsedArgs.url, 1, 'Mon', '05:00', 1).status_code, 201)
    self.assertEqual(rsclient.addSchedule(parsedArgs.url, 2, 'Tue', '06:00', 2).status_code, 201)
    self.assertEqual(rsclient.addSchedule(parsedArgs.url, 3, 'Wed', '07:00', 3).status_code, 201)
    self.assertEqual(rsclient.addSchedule(parsedArgs.url, 3, ['Mon','Tue'], '11:00', 1), None)
    self.assertEqual(rsclient.getSchedule(parsedArgs.url, 1).status_code, 200)
    self.assertEqual(rsclient.getScheduleID(parsedArgs.url), 6)
    self.assertEqual(rsclient.getAllSchedules(parsedArgs.url).status_code, 200)

    # Test get/update/delete w/ schedules
    self.assertEqual(rsclient.getSchedule(parsedArgs.url, 1).status_code, 200)
    self.assertEqual(rsclient.updateSchedule(parsedArgs.url, 1, 'Thu', '05:00', 1).status_code, 201)
    self.assertEqual(rsclient.updateSchedule(parsedArgs.url, 2, 'Tue', '06:01', 2).status_code, 201)
    self.assertEqual(rsclient.updateSchedule(parsedArgs.url, 3, 'Wed', '07:00', 4).status_code, 201)
    self.assertEqual(rsclient.updateSchedule(parsedArgs.url, 3, 'Sun', '12:00', 10).status_code, 201)
    self.assertEqual(rsclient.updateSchedule(parsedArgs.url, 3, weekend, '11:00', 10), None)
    self.assertEqual(rsclient.deleteSchedule(parsedArgs.url, 1).status_code, 204)
    self.assertEqual(rsclient.deleteSchedule(parsedArgs.url, 2).status_code, 204)
    self.assertEqual(rsclient.deleteSchedule(parsedArgs.url, 3).status_code, 204)
    self.assertEqual(rsclient.deleteSchedule(parsedArgs.url, 4).status_code, 204)
    self.assertEqual(rsclient.deleteSchedule(parsedArgs.url, 5).status_code, 204)
    self.assertEqual(rsclient.getScheduleID(parsedArgs.url), 1)
    self.assertEqual(rsclient.getAllSchedules(parsedArgs.url).status_code, 404)

    # Test delete sprinkler to remove schedules
    self.assertEqual(rsclient.addSchedule(parsedArgs.url, 1, 'Mon', '05:00', 1).status_code, 201)
    self.assertEqual(rsclient.deleteSprinkler(parsedArgs.url, 1).status_code, 204)
    self.assertEqual(rsclient.getSchedule(parsedArgs.url, 1).status_code, 404)

  def test_RainDelay(self):
    # Test get/patch/delete raindelay
    self.assertEqual(rsclient.getRainDelay(parsedArgs.url).status_code, 200)
    self.assertEqual(rsclient.patchRainDelay(parsedArgs.url).status_code, 201)
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler1', 10).status_code, 201)
    self.assertEqual(rsclient.addSchedule(parsedArgs.url, 1, datetime.now().strftime("%a"), datetime.now().strftime("%H:%M"), 1).status_code, 201)
    self.assertEqual(rsclient.runSchedule(parsedArgs.url, 1).status_code, 202)
    self.assertEqual(rsclient.deleteRainDelay(parsedArgs.url).status_code, 204)

  def test_runAdhoc(self):
    # Test with no sprinklers
    self.assertEqual(rsclient.runAdhoc(parsedArgs.url, 1, 5).status_code, 404)

    # Test with sprinkler
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler1', 10).status_code, 201)
    self.assertEqual(rsclient.runAdhoc(parsedArgs.url, 1, 1).status_code, 200)
    time.sleep(2)

    # Test stopping sprinkler
    self.assertEqual(rsclient.runAdhoc(parsedArgs.url, 1, 5).status_code, 200)
    self.assertEqual(rsclient.stopRunning(parsedArgs.url).status_code, 200)
    time.sleep(2)

  def test_runSchedule(self):
    # Test with no schedule
    self.assertEqual(rsclient.runSchedule(parsedArgs.url, 1).status_code, 404)

    # Test with schedule
    self.assertEqual(rsclient.addSprinkler(parsedArgs.url, 'sprinkler1', 10).status_code, 201)
    self.assertEqual(rsclient.addSchedule(parsedArgs.url, 1, 'Mon', '05:00', 1).status_code, 201)
    self.assertEqual(rsclient.runSchedule(parsedArgs.url, 1).status_code, 200)
    time.sleep(2)

if __name__ == '__main__':
  argParser = argparse.ArgumentParser(description="Raspberry Sprinkles Unit Testing")
  #argParser.add_argument("-f", "--flog", help="Path to unittest Flask log file", default='/var/log/rs/flask.log')
  #argParser.add_argument("-l", "--rslog", help="Path to unittest Raspberry Sprinkles log file", default='/var/log/rs/raspberry-sprinkles.log')
  argParser.add_argument("-s", "--schedule", help="schedule file", default='unit_testing_schedule.json')
  argParser.add_argument("-u", "--url", help="base url", default='http://127.0.0.1:5000/')
  parsedArgs = argParser.parse_args()
  finalResult = True
  unittest.main(exit=True)
  print(finalResult)