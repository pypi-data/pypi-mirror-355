import unittest
from libumd import Loader

class libumd_test(unittest.TestCase):
    def test_basic_case(self):
        loader = Loader()
        loader.setparams('name', 'John')
        mod = loader.loadmod('greeter')
        mod.start()
        mod.greet()
        mod.stop()

    def test_edge_case(self):
        loader = Loader()
        loader.setparams('name', 'John')
        mod = loader.loadmod('greeter')
        mod.start()
        mod.greet()
        print(mod.status())
        mod.stop()

if __name__ == '__main__':
    unittest.main()