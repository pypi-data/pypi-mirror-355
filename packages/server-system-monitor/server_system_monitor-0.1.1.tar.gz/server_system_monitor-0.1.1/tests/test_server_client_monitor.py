import unittest
from server_system_monitor import ServerClientMonitor 

class TestServerClientMonitor(unittest.TestCase):
    def test_can_connect_via_password(self):
        client = ServerClientMonitor.from_user_password('127.0.0.1','root','root',2222)

    def test_send_ram(self):
        client = ServerClientMonitor.from_user_password('127.0.0.1','root','root',2222)

        self.assertListEqual(list( client.send_ram().keys()),[
            'total',
            'used',
            'free',
            'shared',
            'buff/cache',
            'available'])

    def test_send_cpu(self):
        client = ServerClientMonitor.from_user_password('127.0.0.1','root','root',2222)

        self.assertListEqual(list(client.send_stats().keys()),[
            'cpu',
            'usr',
            'nice',
            'sys',
            'iowait',
            'irq',
            'soft',
            'steal',
            'guest',
            'gnice',
            'idle'])
        


if __name__ == '__main__':
    unittest.main()