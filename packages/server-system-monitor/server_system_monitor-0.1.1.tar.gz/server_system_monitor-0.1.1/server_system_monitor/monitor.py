from server_system_monitor import ServerClientMonitor,ConnectionMonitor
from typing import Self

class Monitor:

    def __init__(self,connection_monitor:ConnectionMonitor,server_client_monitor:ServerClientMonitor):
        
        self.server_client = server_client_monitor
        self.connection = connection_monitor

    @staticmethod
    def from_user_password(hostname:str,password:str,username:str,port:int = 22)->Self:

        return Monitor(ConnectionMonitor(hostname),ServerClientMonitor.from_user_password(hostname,password,username,port))