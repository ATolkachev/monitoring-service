import unittest

class TestMethods(unittest.TestCase):

    def test_1(self):
        self.assertTrue(True)
        self.assertEqual(2,2)


if __name__ == '__main__':
    unittest.main()