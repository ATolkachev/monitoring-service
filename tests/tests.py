import unittest
from monitor import checker,rest
import json
from time import time

class TestMethods(unittest.TestCase):

    # def test_check(self):
    #     self.check = checker.CheckerService()
    #     self.check.start_monitors()

    def test_rest(self):
        self.rest = rest.RestService()

        check_dict = {"name": "Foo", "address": "127.0.0.1", "port": 80, "alive": False, "since": int(time()), "enabled": True, "id": 1}

        self.assertDictEqual(self.rest.check_insert_monitor(check_dict),check_dict)

        self.assertTrue(self.rest.get_max_monitor_id() == 0)

        self.rest.insert_monitor(check_dict)

        self.assertDictEqual(json.dumps({"items": [check_dict]}),self.rest.get_all_checks())

        self.assertDictEqual(self.rest.get_check_status(1), check_dict)

        self.assertTrue(self.rest.get_max_monitor_id()==1)

if __name__ == '__main__':
    unittest.main()