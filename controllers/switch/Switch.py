
from typing import Dict, List
from Errors.NetControlExceptions import NoController, TelnetNoAuthDataException
from Router import Router
from models.models import Model
from service.Snmp import Snmp
import telnetlib

import settings

class SwitchController:
    def __init__(self,snmp_con: Snmp, telnet_data: Dict) -> None:
        self.snmp_con: Snmp = snmp_con
        self.telnet_data: Dict = telnet_data
        self.ports: Dict[str,Dict[str,str]] = {}
    
    #override
    def get_arp_table(self) -> List[dict]:
        pass
    
    #override
    def get_switchport_mode_on_port(self,port) -> str:
        pass
    
    #override
    def get_access_vlan_on_port(self,port) -> List[str]:
        pass
    
    #override
    def get_switchport_mode_on_all_ports(self) -> dict:
        pass
    
    def get_ports(self) -> Dict[str,Dict[str,str]]:
        return self.ports
        
    def get_ifname(self,port: str) -> str:
        if not self.ports.get(port):
            raise Exception('Port not find')
        
        index = self.ports[port]['index']    
        data = self.snmp_con.get([f'1.3.6.1.2.1.31.1.1.1.1.{index}'])[0]
        if data[1]:  
            return data[1]
    
    def get_port_status(self,port: str) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')

        index = self.ports[port]['index']
        data = self.snmp_con.get([f'1.3.6.1.2.1.2.2.1.8.{index}'])[0]
        
        return True if data[1] == '1' else False
    
    def get_all_ports_status(self) -> List[bool]:
        oids = [ '1.3.6.1.2.1.2.2.1.8.' + self.ports[port]['index'] for port in self.ports ]

        data = self.snmp_con.get(oids)
        res = []
        
        for val in data:
            res.append( True if val[1] == '1' else False )
        
        return res
    
    
    def get_ifdescr(self,port: str):
        if not self.ports.get(port):
            raise Exception('Port not find')

        index = self.ports[port]['index']    
        data = self.snmp_con.get([f'1.3.6.1.2.1.31.1.1.1.18.{index}'])[0]
       
        return data[1]
    
    def get_all_ifdescr(self) -> List[str]:
        oids = [ '1.3.6.1.2.1.31.1.1.1.18.' + self.ports[port]['index'] for port in self.ports ]
        data = self.snmp_con.get(oids)
        res = []
        
        for val in data:
            res.append( val[1] )
        
        return res


    def get_admin_port_status(self,port: str) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')

        index = self.ports[port]['index']
        data = self.snmp_con.get([f'1.3.6.1.2.1.2.2.1.7.{index}'])[0]
      
        return True if data[1] == '1' else False
    
    def get_admin_all_ports_status(self) -> List[bool]:
        oids = [ '1.3.6.1.2.1.2.2.1.7.' + self.ports[port]['index'] for port in self.ports ]

        data = self.snmp_con.get(oids)
        res = []
        
        for val in data:
            res.append( True if val[1] == '1' else False )
        
        return res
    
    def perttier_vlan(self,vlans):
        data = []
        temp = []
        
        for i in range(len(vlans)):
            if i+1 == len(vlans):
                temp.append(vlans[i])
                data.append(temp)
                temp = []
            else:
                if int(vlans[i+1]) - int(vlans[i]) == 1:
                    temp.append(vlans[i])
                else:
                    temp.append(vlans[i])
                    data.append(temp)
                    temp = []
        
        return list(map(lambda x: f'{x[0]}-{x[-1]}' if len(x) > 1  else x[0],data))
    
    #override
    def get_vlans_on_port(self,index: str) -> List[str]:
        pass
    
    #override
    def get_ports_on_vlan(self,vlan) -> List[str]:
        pass
    
    #override
    def get_vlans_on_all_ports() -> List[List[str]]:
        pass
    
    #override
    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]):
        pass
    
    #override
    def delete_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        pass
    
    #override
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        pass
    
    
    def get_all_info_ports(self) -> List[Dict]:
        data = []
        admin_ports_status = self.get_admin_all_ports_status()
        ports_status = self.get_all_ports_status()
        ifdescrs = self.get_all_ifdescr()
        vlans = self.get_vlans_on_all_ports()
        names = [ self.ports[port]['name'] for port in self.ports ]
        for ind in range(len(names)): 
            data.append({
                'name': names[ind],
                'A_status': admin_ports_status[ind],
                'status': ports_status[ind],
                'descr' : ifdescrs[ind],
                'vlans': self.perttier_vlan(vlans[ind])
            })
        
        return data
    
    
    
    
    def convert_mac(self,dec_mac):
        return ':'.join( list(map(lambda x: hex(int(x))[2:].zfill(2).upper(),dec_mac)) )
    
    def convert_hexmac_to_decmac(self,hex_mac):
        return '.'.join( list(map(lambda x: str( int(x,16) ),hex_mac.split(':'))) )
    
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

    def _chunks(self,lst, n):
      for i in range(0, len(lst), n):
         yield lst[i:i + n]

    def _convert_bin_to_hex(self,bin_values):
       bin_values = tuple(self._chunks(bin_values,4))
       return ''.join( list(map(lambda x: hex(int(x,2))[2:],bin_values)) )
   
    
    def get_self_mac_from_arp_router(self):
        gateway_ip = '.'.join( self.snmp_con.host.split('.')[:-1] + ['254'] )
        try:
            router = Router(gateway_ip,'gateway','unknown',settings.RO_COMMUNITY,settings.USERNAME_GATEWAY,settings.PASSWORD_GATEWAY,settings.ENABLE_GATEWAY)
            return router.get_mac_from_ip(self.snmp_con.session.hostname)
        except Exception as e:
            print(e)
            return self.get_self_mac()
    
    
    def get_mac_gateway(self) ->str:
        gateway_ip = '.'.join( self.snmp_con.host.split('.')[:-1] + ['254'] )
        try:
            router = Router(gateway_ip,'unknown',Model.UNKNOWN,settings.RO_COMMUNITY,settings.USERNAME_GATEWAY,settings.PASSWORD_GATEWAY,settings.ENABLE_GATEWAY)
            data = router.get_mac_from_ip(gateway_ip)
            return data
        except NoController:
            print(gateway_ip, 'is not Router')
            data = self.get_mac_from_ip(gateway_ip)
            return data
            
    
    
    def get_self_mac(self) -> str:
        self_mac = ''
        oid = '1.3.6.1.2.1.17.7.1.2.2.1.2'
        data = self.snmp_con.walk_untill_value_contains(oid,'0')
        if data:
            dec_mac = data[0].split('.')[-6:]
            hex_mac = self.convert_mac(dec_mac)
            self_mac = hex_mac
            
        return self_mac
    
    def get_mac_from_ip(self,ip):
        data = list(filter(lambda x: x[0] == ip,self.get_macs_and_ips()))
        if data:
            return data[0][1]
        else:
            return ''
    
    def get_macs_and_ips(self):
        data = self.snmp_con.walk_oid_value('1.3.6.1.2.1.4.22.1.2')
        data = list( map( lambda x: ( '.'.join( x[0].split('.')[-4:] ), ':'.join( self._chunks( x[1][2:],2 ) ).upper() ), data ) )
        return data

    def get_macs_vlan(self,vlan):
        macs = []
        dec_macs = self.snmp_con.walk_index_value(f'1.3.6.1.2.1.17.7.1.2.2.1.2.{vlan}')
        for dec_mac_port in dec_macs:
            dec_mac = dec_mac_port[0].split('.')[-6:]
            port_index = dec_mac_port[1]
            macs.append( (port_index, self.convert_mac(dec_mac)) )
        
        return macs
    
    def get_all_macs_on_ports(self):
        data = self.snmp_con.walk_oid_value('1.3.6.1.2.1.17.4.3.1.2')
        if 'NO' not in data:
            return list(map(lambda x: (  self.convert_mac(x[0].split('.')[-6:]), x[1] ),data))
        return []

    def get_macs_from_port(self,port):
        if not self.ports.get(port):
            raise Exception('Port not find')
        
        index = self.ports[port]['index']  
        vlans = self.get_vlans_on_port(port)
        macs = []
        for vlan in vlans:
            macs_on_vlan = self.get_macs_vlan(vlan)
            for index_mac in macs_on_vlan:
                if index == index_mac[0]:
                    macs.append(index_mac[1])
        
        return macs
    
    def get_port_from_mac(self,hexmac):
        decmac = self.convert_hexmac_to_decmac(hexmac)
        data = self.snmp_con.get([f'1.3.6.1.2.1.17.4.3.1.2.{decmac}'])
        if data:
            return data[0][1]
        return ''

    def get_uplink_port(self):
        try:
            gateway_mac = self.get_mac_gateway()
            index = self.get_port_from_mac(gateway_mac)
      
            if index:
                return [ i for i in self.ports if self.ports[i]['index'] == index ][0]
            
        except Exception as e:
            print('get uplink port ',e)
            return None
        
class TELNETController:
    def __init__(self,ports: list,ip,login,passwords,enable) -> None:
        #@overide
        self.connection = None
        self.ip = ip
        self.login = login
        self.passwords = passwords
        self.enable = enable
        self.ports: list = ports
        self.res = []
    
    @staticmethod
    def request(method):
        def wrapper(*args, **kwargs):
            self = args[0]
            
            if all([self.ip,self.login,self.passwords,self.enable]):
                self.start()
                return_value = method(*args,**kwargs)
                self.close()
                return return_value
            else:
                raise TelnetNoAuthDataException("NO AUTH DATA")

        return wrapper

    def start(self):
        self.connection = telnetlib.Telnet(self.ip)
        self.enter()

    def enter(self):
        pass
    
    def enter_command(self,command):
        pass
    
    def close(self):
        self.connection.close()

    def to_bytes(self,line):
        return f"{line}\r\n".encode("utf-8")