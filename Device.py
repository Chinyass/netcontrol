import ipaddress
from pythonping import ping
from service.Snmp import Snmp

from models.models import Model

from typing import Tuple

class Device:
    def __init__(self,ip: str,name: str, model: Model, communty: str=None , username: str =None, passwords: list=None,enable: str=None ) -> None:
        self.ip = ipaddress.ip_address(ip) #validate
        self.ip: str = str(self.ip)
        self.name: str = name
        self.model: Model = model
        self.community: str = communty
        self.username: str = username
        self.passwords: list = passwords
        self.enable: str = enable
        self.snmp: Snmp = Snmp(self.ip,self.community)
        
        self.ping: bool = False
        self.snmp_status: bool = False
        self.uplink: str = None
        self.mac: str = None
        self.sysdescription: str = None
        
        self.update_ping_status()
        if self.ping:
            self.update_snmp_status()
    
    def update_ping_status(self) -> None:
        self.ping = ping(self.ip,count=2).success()
    
    def update_snmp_status(self) -> None:
        try:
            data = self.get_sysdescr()
            if data[1]:
                self.sysdescription = data[1]
                self.snmp_status = True
                
        except Exception as e:
            print(self.ip, e)
            self.snmp_status = False
    
    def get_sysdescr(self) -> Tuple[str,str]:
            return self.snmp.get(['1.3.6.1.2.1.1.1.0'])[0]
        
       
if __name__ == '__main__':
    pass