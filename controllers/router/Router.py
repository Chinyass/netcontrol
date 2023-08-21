from typing import Dict, List
from Errors.NetControlExceptions import TelnetNoAuthDataException
from service.Snmp import Snmp
import telnetlib

class RouterController:
    def __init__(self,snmp_con: Snmp, telnet_data: Dict) -> None:
        self.snmp_con: Snmp = snmp_con
        self.telnet_data: Dict = telnet_data
        self.ports: Dict[str,Dict[str,str]] = {}
    
    def _convert_to_hex(self,bytes):
        s = ""
        for i in bytes:
            s += ("%0.2X" % ord(i))
        return s
    
    def _convert_hex_to_bin(self,hex_values):
        temp = []
        for i in range(0,len(hex_values)):
          temp.append( bin(int(hex_values[i], 16))[2:].zfill(4) )
     
        return ''.join(temp)
    
    def convert_mac(self,dec_mac):
        return ':'.join( list(map(lambda x: hex(int(x))[2:].zfill(2).upper(),dec_mac)) )
    
    def _chunks(self,lst, n):
      for i in range(0, len(lst), n):
         yield lst[i:i + n]
    
    def get_allports(self) -> List[tuple]:
        data = self.snmp_con.walk_index_value('1.3.6.1.2.1.31.1.1.1.1')
        return data
    
    def get_mac_from_ip(self,ip) -> str:
        ports = [ i[0] for i in self.get_allports() ]
        for port in ports:
            data = self.snmp_con.get([f'1.3.6.1.2.1.3.1.1.2.{port}.1.{ip}'])
            if data:
                data = data[0]
                if data[1]:
                    return ':'.join(tuple(self._chunks( self._convert_to_hex(data[1]),2 )))
                
        return None
    