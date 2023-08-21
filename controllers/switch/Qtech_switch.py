import re
from typing import Dict, List, Tuple
import time
from Errors.NetControlExceptions import NoController, SnmpTooBigException
from Router import Router
from controllers.switch.Switch import SwitchController, TELNETController
from models.models import Model
from service.Snmp import Snmp

import settings

class QSW2850_28(SwitchController):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( [ ( str(i), {'index': str(i),'name' : f'eth1/0/{i}' } ) for i in range(1,29) ] )
        self.telnet_con = QSW2850_28_TELNET(self.ports,**telnet_data)
    
    def get_arp_table(self) -> List[dict]:
        return self.telnet_con.get_arp_table()
    
    def get_switchport_mode_on_port(self,port) -> str:
        return self.telnet_con.get_switchport_mode_on_port(port)
    
    def get_switchport_mode_on_all_ports(self) -> dict:
        return self.telnet_con.get_switchport_mode_on_all_ports()
    
    def get_vlans_on_port(self,port) -> List[str]:
        return self.get_trunk_vlans_on_port(port) + self.get_access_vlan_on_port(port)
    
    def get_ports_on_vlan(self,vlan) -> List[str]:
        vlan = vlan.strip()
        hex_ports = self._convert_to_hex(self.snmp_con.get([f'1.3.6.1.2.1.17.7.1.4.3.1.2.{vlan}'])[0][1])
        print(hex_ports)
        if not hex_ports:
            return []
        
        bin_ports = self._convert_hex_to_bin(hex_ports)
        ports = []
        for i in range(len(bin_ports)):
            if bin_ports[i] == '1':
                ports.append(str(i+1))
        return ports
    
    def get_vlans_on_all_ports(self) -> List[List[str]]:
        res = []
        trunks = self.get_trunk_vlans_on_all_ports()
        acess = self.get_access_vlan_on_all_ports()
        
        for index in range(len(self.ports)):
            res.append( trunks[index] + acess[index]  )
        
        return res
    
    def get_trunk_vlans_on_port(self,port :str) -> List[str]:
        if not self.ports.get(port):
            raise Exception('Port not find')

        vlans = []
        index = self.ports[port]['index']
        data = self.snmp_con.get([f'1.3.6.1.4.1.27514.100.3.2.1.20.{index}'])
        if data:
            hex_vlans = self._convert_to_hex(data[0][1])
            bin_vlans = self._convert_hex_to_bin(hex_vlans)
            
            for i in range(len(bin_vlans)):
                if bin_vlans[i] == '1':
                    vlans.append(str(i))
                
        return vlans
    
    def get_trunk_vlans_on_all_ports(self) -> List[List[str]]:
        oids = [ '1.3.6.1.4.1.27514.100.3.2.1.20.' + self.ports[port]['index'] for port in self.ports ]
        try:
            data = self.snmp_con.get(oids)
        except SnmpTooBigException as e:
            print(self.snmp_con.host, e)
            data = []
            oids_chunk = tuple(self._chunks(oids,15))
            for oids in oids_chunk:
                data+=self.snmp_con.get(oids)
                
        res = []
        if data:
            for value in data:
                vlans = []
                hex_vlans = self._convert_to_hex(value[1])
                bin_vlans = self._convert_hex_to_bin(hex_vlans)
                
                for i in range(len(bin_vlans)):
                    if bin_vlans[i] == '1':
                        vlans.append(str(i))
                
                res.append(vlans)
                
        return res
                
    def get_access_vlan_on_port(self,port) -> List['str']:
        if not self.ports.get(port):
            raise Exception('Port not find')
        vlans = []
        data = self.snmp_con.get([f'1.3.6.1.2.1.17.7.1.4.5.1.1.{port}'])
        if data:
            vlan = data[0][1]
            if vlan != '1':
                vlans.append(vlan)
        
        return vlans

    def get_access_vlan_on_all_ports(self) -> List[List[str]]:
        oids = [ f'1.3.6.1.2.1.17.7.1.4.5.1.1.{port}' for port in self.ports ]
        data = self.snmp_con.get(oids)
        if data:
            return [ [x[1]] for x in data ]
        else:
            return []
    
    def create_vlan(self,vlan):
        try:
            res = self.snmp_con.set_int(f'1.3.6.1.4.1.27514.100.5.1.1.4.{vlan}','1')
        except Exception as e:
            print(self.snmp_con.host, e)
            return False
        
        return True
    
    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')

        index = self.ports[port]['index']

        created_vlans = []
        for vlan in vlans:
            created_vlans.append( self.create_vlan(vlan) )
        
        if all(created_vlans):
            exists_vlans = self.get_vlans_on_port(port)
            new_vlans = exists_vlans + vlans
            new_vlans = ','.join(new_vlans)
            try:
                res = self.snmp_con.set_string(f'1.3.6.1.4.1.27514.100.3.2.1.20.{index}',new_vlans)
            except Exception as e:
                print(self.snmp_con.host, e)
                return False
            
            return True
        else:
            print('Error creating vlan')
            return False
    
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')

        if self.create_vlan(vlan):
            try:
                res = self.snmp_con.set_int(f'1.3.6.1.4.1.27514.100.3.2.1.16.{port}',vlan)
            except Exception as e:
                print(self.snmp_con.host, e)
                return False
        
        return True

    def delete_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')

        exists_vlans = self.get_vlans_on_port(port)
        new_vlans = list(filter(lambda x: x not in vlans ,exists_vlans))
        new_vlans = ','.join(new_vlans)
        try:
            res = self.snmp_con.set_string(f'1.3.6.1.4.1.27514.100.3.2.1.20.{port}',new_vlans)
        except Exception as e:
                print(self.snmp_con.host, e)
                return False

        return True


class QSW2850_10(QSW2850_28):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( [ ( str(i), {'index': str(i),'name' : f'eth1/0/{i}' } ) for i in range(1,11) ] )
        self.telnet_con = QSW2850_10_TELNET(self.ports, **telnet_data)

class QSW3470_28(QSW2850_28):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.telnet_con = QSW3470_28_TELNET(self.ports, **telnet_data)

class QSW4610_28(QSW2850_28):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.telnet_con = QSW4610_28_TELNET(self.ports, **telnet_data)

class QSW4610_10(QSW4610_28):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( [ ( str(i), {'index': str(i),'name' : f'eth1/0/{i}' } ) for i in range(1,11) ] )
        self.telnet_con = QSW4610_28_TELNET(self.ports, **telnet_data)

class QSW2800_28(QSW2850_28):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.telnet_con = QSW2800_28_TELNET(self.ports, **telnet_data)
        
    def get_uplink_port(self):
        try:
            gateway_mac = self.get_mac_gateway()
            return self.get_port_from_mac(gateway_mac)
        except Exception as e:
            print('get uplink port ',e)
            return None

class QSW2910_26(SwitchController):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                            [ ( str(i), {'index': str(i),'name' : f'e0/0/{i}' } ) for i in range(1,25) ] +
                            [ ( str(i), {'index': str(i),'name' : f'e0/1/{i-24}' } ) for i in range(25,27) ]
                        )
        self.telnet_con = QSW2910_26_TELNET(self.ports, **telnet_data)
        
    def get_arp_table(self) -> List[dict]:
        return self.telnet_con.get_arp_table()
    
    def get_switchport_mode_on_port(self,port) -> str:
        return self.telnet_con.get_switchport_mode_on_port(port)
    
    def get_switchport_mode_on_all_ports(self) -> dict:
        return self.telnet_con.get_switchport_mode_on_all_ports()
    
    def get_vlans_on_all_ports(self) -> List[List[str]]:
        res = []
        for port in self.ports:
            res.append( self.get_vlans_on_port(port) )
        
        return res
    
    def get_vlans_on_port(self,port) -> List[str]:
        if not self.ports.get(port):
            raise Exception('Port not find')
        data = self.snmp_con.walk_index_value('1.3.6.1.2.1.17.7.1.4.3.1.2')

        data = list(map(lambda x: ( x[0],self._convert_hex_to_bin( x[1][2:] ) ) if x[1] else x, data))
  
        ndata = []
        for i in data:
            vlan = i[0]
            bin_ports = i[1]
            ndata.append( (vlan,self._get_values_from_bin(bin_ports)) )

 
        svlans = list( map( lambda y: y[0], filter(lambda x: port in x[1],ndata) ) )
        return svlans
    
    def get_ports_on_vlan(self,vlan) -> List[str]:
        data = self.snmp_con.get([f'1.3.6.1.2.1.17.7.1.4.3.1.2.{vlan}'])[0][1]
        if not data or 'NO' in data.upper():
            return []
        data = self._convert_hex_to_bin( self._convert_to_hex(data) )
       
        return self._get_values_from_bin(data)
    
    def get_access_vlan_on_port(self,port) -> List[str]:
        if not self.ports.get(port):
            raise Exception('Port not find')
        
        res = self.snmp_con.get([f'1.3.6.1.2.1.17.7.1.4.5.1.1.{port}'])[0][1]
        if not res:
            return []
        
        return [res]

    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')
        
        results = []
        for vlan in vlans:
            created = self.create_vlan(vlan)
            if created:
                hex_ports = self._convert_to_hex(self.snmp_con.get([f'1.3.6.1.2.1.17.7.1.4.3.1.2.{vlan}'])[0][1])
                if not hex_ports:
                    bin_ports = '0' * 16
                else:
                    bin_ports = self._convert_hex_to_bin(hex_ports)
                
                new_bin_ports = ''
                for i,v in enumerate(bin_ports):
                    if (i+1) == int(port):
                        new_bin_ports+='1'
                    else:
                        new_bin_ports+=v

                new_hex_ports = self._convert_bin_to_hex(new_bin_ports)
                try:
                    res = self.snmp_con.set_hexValue(f'1.3.6.1.2.1.17.7.1.4.3.1.2.{vlan}',new_hex_ports)
                    results.append(True)
                except Exception as e:
                    print(self.snmp_con.host, e)
                    results.append(False)
        
        if all(results):
            return True
        
        return False

    #TODO
    def delete_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        pass #raise Exception("this model not function")

    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        return self.set_trunk_vlans_on_port(port,[vlan])
        '''
        if not self.ports.get(port):
            raise Exception('Port not find')
        
        try:
            res = self.snmp_con.set_unsigned(f'1.3.6.1.2.1.17.7.1.4.5.1.1.{port}', vlan)
            return True
        except Exception as e:
            print(self.snmp_con.host, e)
            return False
        '''

    def create_vlan(self,vlan):
        try:
            res = self.snmp_con.set_int(f'1.3.6.1.2.1.17.7.1.4.3.1.5.{vlan}',4)
            return True
        except Exception as e:
            print(self.snmp_con.host,e)
            return False
        
    def _get_values_from_bin(self,data: str):
        res = []
        for j,v in enumerate(data):
            if v == '1':
                res.append(str(j+1))
        
        return res
    
    def get_self_mac(self):
        gateway_ip = '.'.join( self.snmp_con.host.split('.')[:-1] + ['254'] )
        try:
            router = Router(gateway_ip,'unknown',Model.UNKNOWN,settings.RO_COMMUNITY,settings.USERNAME_GATEWAY,settings.PASSWORD_GATEWAY,settings.ENABLE_GATEWAY)
     
            data = router.get_mac_from_ip(self.snmp_con.host)
            return data
        except NoController:
            '''TRY CHANGE CONTROLLER TO ANOTHER SWITCH'''
            print(gateway_ip, 'gw is not Router')
            ip = self.snmp_con.host
            gateway_con = Snmp(gateway_ip,settings.RO_COMMUNITY)
            original_con = self.snmp_con
            self.snmp_con = gateway_con
            data = self.get_mac_from_ip(ip)
            self.snmp_con = original_con
            
            return data
    
    def get_mac_gateway(self):
        gateway_ip = '.'.join( self.snmp_con.host.split('.')[:-1] + ['254'] )
        try:
            router = Router(gateway_ip,'unknown',Model.UNKNOWN,settings.RO_COMMUNITY,settings.USERNAME_GATEWAY,settings.PASSWORD_GATEWAY,settings.ENABLE_GATEWAY)
      
            data = router.get_mac_from_ip(gateway_ip)
            return data
        except NoController:
            '''TRY CHANGE CONTROLLER TO ANOTHER SWITCH'''
            print(gateway_ip, 'gw is not Router')
            ip = self.snmp_con.host
            gateway_con = Snmp(gateway_ip,settings.RO_COMMUNITY)
            original_con = self.snmp_con
            self.snmp_con = gateway_con
            data = super().get_self_mac()
            self.snmp_con = original_con
            
            return data
    
    def get_uplink_port(self):
        try:
            self.get_all_macs_on_ports()
            gateway_mac = self.get_mac_gateway()
            return self.get_port_from_mac(gateway_mac)
        except Exception as e:
            print('get uplink port ',e)
            return None

class QSW2910_28(QSW2910_26):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                            [ ( str(i), {'index': str(i),'name' : f'eth0/0/{i}' } ) for i in range(1,25) ] +
                            [ ( str(i), {'index': str(i),'name' : f'eth0/1/{i-24}' } ) for i in range(25,29) ]
                        )
        
        self.telnet_con = QSW2910_26_TELNET(self.ports, **telnet_data)









class QSW2850_28_TELNET(TELNETController):
    def __init__(self, ports: list,ip, login, passwords, enable, ) -> None:
        super().__init__(ports,ip, login, passwords, enable)
        
    def enter(self):
        self.connection.read_until(b"login:",timeout=3)
        self.connection.write(self.to_bytes(self.login))
        self.connection.read_until(b"Password:",timeout=3)

        for password in self.passwords:
            self.connection.write(self.to_bytes(password))
            index, m, output = self.connection.expect([b"login:", b"#"],timeout=3)
            if index == 1:
                break
            elif index == 0:
                self.connection.write(self.to_bytes(self.login))
                self.connection.read_until(b"Password:",timeout=3)
        else:
            self.close()
            raise Exception('Incorrect password')

        self.connection.write(b"terminal length 0\n")
        self.connection.read_until(b"#", timeout=3)
        time.sleep(2)
        self.connection.read_very_eager()
    
    def enter_command(self,command):
        self.connection.write(self.to_bytes(command))
        out = self.connection.read_until(b"#", timeout=3).decode("utf-8")
        self.res.append(out)
        return out
    
    @TELNETController.request
    def get_config(self):
        data = self.enter_command("show run")
        return data
    
    @TELNETController.request
    def get_arp_table(self):
        data = self.enter_command("show arp")
        data = data.split()
        data = data[25:-1]
        devices = list(zip(*[iter(data)]*6))
        data = []
        for device in devices:
            data.append({
                'ip': device[0],
                'mac': device[1].replace('-',':'),
                'vlan': device[2].replace('Vlan',''),
                'port': device[3].replace('Ethernet1/0/','')
            })
        return data

    
    def get_uplink_port(self):
        arp = self.get_arp_table()
  
        gateway_ip = '.'.join(self.ip.split('.')[:-1] + ['254'])
        up_port = list(filter(lambda x: x['ip'] ==  gateway_ip,arp))
     
        if up_port:
            return up_port[0]['port']
        return False
    
    @TELNETController.request
    def set_snmp_community(self,community):
        print( self.enter_command('config') )
        print( self.enter_command('snmp-server enable') )
        print( self.enter_command('snmp-server securityip disable') )
        print( self.enter_command(f'snmp-server community rw 0 {community}') )
        print( self.enter_command('exit') )
        print( self.enter_command('wr') )
        print( self.enter_command('y') )

        return True
    
    @TELNETController.request
    def get_switchport_mode_on_port(self,port) -> str:
        port_name = self.ports[port]['name']
        data = self.enter_command(f"show run int {port_name}")
        data = data.split('\n')
        data = list(filter(lambda x: 'switchport' in x,data))
        if data:
            data = data[0]
            if 'trunk' in data:
                return 'trunk'
            elif 'access' in data:
                return 'access'
            else:
                return 'unknown'
        else:
            raise Exception("Telnet controller send incorrect data in get switchport mode")
    
    @TELNETController.request
    def get_switchport_mode_on_all_ports(self) -> dict:
        res = {}
        for port in self.ports:
            port_name = self.ports[port]['name']
            data = self.enter_command(f"show run int {port_name}")
            data = data.split('\n')
            data = list(filter(lambda x: 'switchport' in x,data))
            if data:
                data = data[0]
                if 'trunk' in data:
                    res[port] = 'trunk'
                elif 'access' in data:
                    res[port] = 'access'
                else:
                    res[port] = 'unknown'
            else:
                res[port] = 'unknown'
                #raise Exception("Telnet controller send incorrect data in get switchport mode")
        
        return res

class QSW2850_10_TELNET(QSW2850_28_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)

class QSW3470_28_TELNET(QSW2850_28_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)

class QSW4610_28_TELNET(QSW2850_28_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)

class QSW2800_28_TELNET(QSW2850_28_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)


class QSW2910_26_TELNET(TELNETController):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    def enter(self):
        self.connection.read_until(b":",timeout=3)
        self.connection.write(self.to_bytes(self.login))
        self.connection.read_until(b":",timeout=3)

        for password in self.passwords:
            self.connection.write(self.to_bytes(password))
            index, m, output = self.connection.expect([b":", b">"],timeout=3)
            if index == 1:
                break
            elif index == 0:
                self.connection.write(self.to_bytes(self.login))
                self.connection.read_until(b":",timeout=3)
        else:
            self.close()
            raise Exception('Incorrect password')

        self.connection.write(b" \n")

        index, m, output = self.connection.expect([b">", b"#"],timeout=3)
        if index == 0:
            self.connection.write(b"enable\n")
            self.connection.write(self.to_bytes(self.enable))
            self.connection.read_until(b"#", timeout=3)
            
        self.connection.write(b"terminal length 0\n")
        self.connection.read_until(b"#", timeout=5)
        time.sleep(2)
        self.connection.read_very_eager()
    
    def enter_command(self,command):
        self.connection.write(self.to_bytes(command))
        out = self.connection.read_until(b"#", timeout=5).decode("utf-8")
        self.res.append(out)
        return out
    
    @TELNETController.request
    def get_config(self):
        res = ''
        self.connection.write(self.to_bytes('show run'))
        while True:
            index, match, output = self.connection.expect([b"....press ENTER", b"#"], timeout=5)
            output = output.decode("utf-8")
            output = re.sub(" ....press ENTER +\x08+ +\x08+", "\n", output)
            res += output
            if index in (1, -1):
                break
            self.connection.write(b" ")
            time.sleep(1)

        return res
    
    @TELNETController.request
    def get_arp_table(self):
        data = self.enter_command("show arp all")
        data = data.split()
        data = data[25:-3]
        devices = list(zip(*[iter(data)]*7))
        data = []
        for device in devices:
            port = list(filter(lambda x: device[3] == self.ports[x]['name'],self.ports))
            if port:
                port = port[0]
            data.append({
                'ip': device[0],
                'mac': device[1],
                'vlan': device[2],
                'port': port
            })
            
        return data
    
    @TELNETController.request
    def set_snmp_community(self,community):
        print( self.enter_command('configure terminal ') )
        print( self.enter_command('snmp-server enable') )
        print( self.enter_command(f'snmp-server community {community} rw permit') )
        print( self.enter_command('exit') )
        print( self.enter_command('copy running-config startup-config') )
        print( self.enter_command('y') )

        return True
    
    @TELNETController.request
    def get_switchport_mode_on_port(self,port) -> str:
        port_name:str = self.ports[port]['name']
        data = self.enter_command(f"show running-config interface ethernet {port_name.replace('e','')}")
        data = data.split('\n')
        data = list(filter(lambda x: 'switchport' in x,data))
        if data:
            data = data[0]
            if 'trunk' in data:
                return 'trunk'
            elif 'default' in data:
                return 'access'
            else:
                return 'unknown'
        else:
            raise Exception("Telnet controller send incorrect data in get switchport mode")
    
    @TELNETController.request
    def get_switchport_mode_on_all_ports(self) -> dict:
        res = {}
        for port in self.ports:
            port_name = self.ports[port]['name']
            data = self.enter_command(f"show running-config interface ethernet {port_name.replace('e','')}")
            data = data.split('\n')
            data = list(filter(lambda x: 'switchport' in x,data))
            if data:
                data = data[0]
                if 'trunk' in data:
                    res[port] = 'trunk'
                elif 'default' in data:
                    res[port] = 'access'
                else:
                    res[port] = 'unknown'
            else:
                res[port] = 'unknown'
                #raise Exception("Telnet controller send incorrect data in get switchport mode")
        return res
    
        
    
if __name__ == '__main__':
    snmp = Snmp('10.3.0.27',settings.RO_COMMUNITY)
    sw = QSW2850_28(snmp,None)
    sw.get_ifname('1')