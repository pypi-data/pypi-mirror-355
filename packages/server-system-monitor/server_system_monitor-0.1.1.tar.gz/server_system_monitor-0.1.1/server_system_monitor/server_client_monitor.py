import json.tool
import paramiko
import re
import json
from typing import Self

class ServerClientMonitor:
    def __init__(self,client:paramiko.SSHClient):
    
        self._conn = client

    @staticmethod
    def from_user_password(hostname:str,password:str,username:str,port:int = 22)->Self:
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(hostname=hostname,password=password,username=username,port=port)

        return ServerClientMonitor(conn)
        
    def send_ram(self)->dict:
        """
        this method is a wrapper for the 'free' linux command
        """
        stdin , out, er = self._conn.exec_command("free")

        error = er.read().decode()

        if error:
            raise ConnectionError(error)
        
        lines = out.read().decode().splitlines()

        out.close(),er.close(),stdin.close()
        
        data_line = re.sub(r'\s+','+',lines[1])

        del lines,out,er,stdin

        data_line = data_line.replace("Mem:+","")
        data_sections = data_line.split("+")
        out = {
            "total":int(data_sections[0]),
            "used":int(data_sections[1]),
            "free":int(data_sections[2]),
            "shared":int(data_sections[3]),
            "buff/cache":int(data_sections[4]),
            "available":int(data_sections[5])
        }

        return out
    

    def send_stats(self)->dict:
        """
        this method is a wrapper for the 'mpstat' linux command of 'sysstat'.

        returns a dict like:
        ```python
        {
            'cpu':float,
            'usr':float,
            'nice':float,
            'sys':float,
            'iowait':float,
            'irq':float,
            'soft':float,
            'steal':float,
            'guest':float,
            'gnice':float,
            'idle':float,
        }
        """
        stdin , out, er = self._conn.exec_command("mpstat -o JSON")

        error = er.read().decode()

        if error:
            raise ConnectionError(error)
        
        ret = json.loads(out.read().decode())['sysstat']['hosts'][-1]['statistics'][-1]['cpu-load'][-1]

        stdin.close(), out.close(), er.close()

        return ret     

    def __del__(self):
        self._conn.close()