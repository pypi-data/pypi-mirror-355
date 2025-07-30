import os
import re

class ConnectionMonitor:
    def __init__(self,hostname:str):
        self.__hostname = hostname

    def get_ping(self,count:int = 1, size:int = 56, interval:float = 1.0)->dict:
        """
        this method is a wrapper for the 'ping' linux command
        """
        process = os.popen(f"ping -q {self.__hostname} -c {count} -s {size} -i {interval:.4f}")
        lines = process.read().splitlines()

        process.close()
        
        if not lines[-1] :
            raise ConnectionError("could not send any data packet")

        data_packets_line = re.split(r'[^0-9]+',lines[3])
        response_time_line = lines[-1].removeprefix("rtt min/avg/max/mdev = ").removesuffix(" ms").split("/")

        return {
            "transmitted":int(data_packets_line[0]),
            "received":int(data_packets_line[1]),
            "min":float(response_time_line[0]),
            "avg":float(response_time_line[1]),
            "max":float(response_time_line[2]),
        }

    def get_hostname(self)->str:
        """
        this method returns the hostname of the connection
        """
        return self.__hostname