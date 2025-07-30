import unittest
from server_system_monitor import ConnectionMonitor

class TestConnectionMonitor(unittest.TestCase):
    def test_can_init(self):
        monitor = ConnectionMonitor("127.0.0.1")

    def test_send_ram(self):
        monitor = ConnectionMonitor("127.0.0.1")

        self.assertListEqual(list( monitor.get_ping().keys()),['transmitted', 'received', 'min', 'avg', 'max'])
        


if __name__ == '__main__':
    unittest.main()