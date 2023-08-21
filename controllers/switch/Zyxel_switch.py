import re
import time
from typing import Dict, List
from Errors.NetControlExceptions import NoController
from Router import Router
from controllers.switch.Switch import SwitchController, TELNETController
from models.models import Model
from service.Snmp import Snmp

import settings

class ZYXEL2108(SwitchController):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                            [ ( str(i), {'index': str(i),'name' : f'port-channel {i}' } ) for i in range(1,10) ]
                    )
        
        self.telnet_con = ZYXEL2108_TELNET(self.ports, **telnet_data)
        
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
        return list(set(self.get_trunk_vlans_on_port(port) + self.get_access_vlan_on_port(port)))
    
    def get_trunk_vlans_on_port(self,port :str) -> List[str]:
        if not self.ports.get(port):
            raise Exception('Port not found')
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
                    print(self.snmp_con.host,e)
                    results.append(False)
            else:
                results.append(False)
        
        if all(results):
            return True
        
        return False
    
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')
        created = self.create_vlan(vlan)
        if created:
            try:
                res = self.snmp_con.set_int(f'1.3.6.1.2.1.17.7.1.4.5.1.1.{port}', vlan)
                return True
            except Exception as e:
                print(self.snmp_con.host,e)
                return False
        else:
            return False
    
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

class ZYXEL2024(ZYXEL2108):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                        [ ( str(i), {'index': str(i),'name' : f'port-channel {i}' } ) for i in range(1,27) ]
                    )
        self.telnet_con = ZYXEL2024_TELNET(self.ports, **telnet_data)
    
    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        return self.telnet_con.set_trunk_vlans_on_port(port,vlans)
    
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        return self.telnet_con.set_access_vlan_on_port(port,vlan)


class ZYXELMES3528(ZYXEL2108):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                        [ ( str(i), {'index': str(i),'name' : f'port-channel {i}' } ) for i in range(1,29) ]
                    )
        self.telnet_con = ZYXELMES3528_TELNET(self.ports, **telnet_data)
    
    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        return self.telnet_con.set_trunk_vlans_on_port(port,vlans)
    
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        return self.telnet_con.set_access_vlan_on_port(port,vlan)


class ZYXELMES3500_24(ZYXEL2108):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                        [ ( str(i), {'index': str(i),'name' : f'port-channel {i}' } ) for i in range(1,29) ]
                    )
        self.telnet_con = ZYXELMES3500_24_TELNET(self.ports, **telnet_data)
    
    def get_mac_gateway(self) ->str:
        gateway_ip = '.'.join( self.snmp_con.host.split('.')[:-1] + ['254'] )
        data = self.telnet_con.get_arp_table()
        uplink = list(filter(lambda x: x['ip'] == gateway_ip,data))
        if uplink:
            uplink = uplink[0]
            return uplink['mac']
        else:
            return ''
    
    def get_uplink_port(self) -> str:
        gateway_ip = '.'.join( self.snmp_con.host.split('.')[:-1] + ['254'] )
        data = self.telnet_con.get_arp_table()
        uplink = list(filter(lambda x: x['ip'] == gateway_ip,data))
        if uplink:
            uplink = uplink[0]
            return uplink['port']
        else:
            return ''

class ZYXELMES3500_8(ZYXELMES3500_24):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                        [ ( str(i), {'index': str(i),'name' : f'port-channel {i}' } ) for i in range(1,11) ]
                    )
        self.telnet_con = ZYXELMES3500_8_TELNET(self.ports, **telnet_data)
    
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        return self.telnet_con.set_access_vlan_on_port(port,vlan)
        
class ZYXELXGS4728(ZYXEL2108):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                        [ ( str(i), {'index': str(i),'name' : f'port-channel {i}' } ) for i in range(1,29) ]
                    )
        self.telnet_con = ZYXELXGS4728_TELNET(self.ports, **telnet_data)


class ZYXELMGS3712(ZYXEL2108):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                        [ ( str(i), {'index': str(i),'name' : f'port-channel {i}' } ) for i in range(1,13) ]
                    )
        self.telnet_con = ZYXELMGS3712_TELNET(self.ports, **telnet_data)
        
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        return self.telnet_con.set_access_vlan_on_port(port,vlan)


class ZYXELGS4012(ZYXEL2108):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                        [ ( str(i), {'index': str(i),'name' : f'port-channel {i}' } ) for i in range(1,13) ]
                    )
        self.telnet_con = ZYXELGS4012_TELNET(self.ports, **telnet_data)
    
    def get_port_from_mac(self,hexmac):
        decmac = self.convert_hexmac_to_decmac(hexmac)
        #data = self.con.get(f'1.3.6.1.2.1.17.4.3.1.2.{decmac}')
        data = self.snmp_con.walk_oid_value('1.3.6.1.2.1.17.4.3.1.2')
        data = list(map(lambda x: (  '.'.join( x[0].split('.')[-6:] ), x[1] ),data))
        data = list(filter(lambda x: x[0] == decmac,data))
        if data:
            return data[0][1]
        return ''

class ZYXELIES1248(ZYXEL2108):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                            [ ( str(i), {'index': str(i),'name' : f'adsl{i}' } ) for i in range(1,49) ] +
                            [ ( str(i), {'index': str(i),'name' : f'enet{i-48}' } ) for i in range(49,51) ]
        )
        self.telnet_con = ZYXELIES1248_TELNET(self.ports, **telnet_data)
    

    
    











class ZYXEL2108_TELNET(TELNETController):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    
    def enter(self):
        self.connection.read_until(b"User name:",timeout=3)
        self.connection.write(self.to_bytes(self.login))
        self.connection.read_until(b"Password:",timeout=3)
        
        for password in self.passwords:
            self.connection.write(self.to_bytes(password))
            index, m, output = self.connection.expect([b"Password:", b"#"],timeout=5)
            if index == 1:
                break
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
        data = self.enter_command("show ip arp")
        data = data.split()
        data = data[10:-1]
        devices = list(zip(*[iter(data)]*6))
        data = []
        for device in devices:
            macs_in_vlan = self.enter_command(f'show mac address-table vlan {device[3]}')
            macs_in_vlan = macs_in_vlan.split()[11:-1]
            macs_in_vlan = list(zip(*[iter(macs_in_vlan)]*4))
            port = list(filter(lambda x: x[2] == device[2],macs_in_vlan))
            if port:
                port = port[0][0]
            else:
                port = ''

            data.append({
                'ip': device[1],
                'mac': device[2],
                'vlan': device[3],
                'port': port
            })

        return data
    
    @TELNETController.request
    def set_snmp_community(self,community):
        print( self.enter_command('configure') )
        print( self.enter_command(f'snmp-server set-community {community}') )
        print( self.enter_command('exit') )

        return True
    
    @TELNETController.request
    def get_switchport_mode_on_port(self,port) -> str:
        port_name = self.ports[port]['name']
        data = self.enter_command(f"show running-config interface {port_name}")
        data = data.split('\n')
        #data = list(filter(lambda x: 'switchport' in x,data))
        if data:
            #data = data[0]
            data = ' '.join(data)
            if 'vlan-trunking' in data:
                return 'trunk'
            elif 'pvid' in data:
                return 'access'
            else:
                return 'unknown'
        else:
            return 'unknown'
    
    @TELNETController.request
    def get_switchport_mode_on_all_ports(self) -> dict:
        res = {}
        for port in self.ports:
            port_name = self.ports[port]['name']
            data = self.enter_command(f"show running-config interface {port_name}")
            data = data.split('\n')
            #data = list(filter(lambda x: 'switchport' in x,data))
            if data:
                #data = data[0]
                data = ' '.join(data)
                if 'vlan-trunking' in data:
                    res[port] = 'trunk'
                elif 'pvid' in data:
                    res[port] = 'access'
                else:
                    res[port] = 'unknown'
            else:
                res[port] = 'unknown'
        
        return res
    
    @TELNETController.request
    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        self.enter_command('configure')
        for vlan in vlans:
            self.enter_command(f'vlan {vlan}')
            self.enter_command(f'fixed {port}')
            self.enter_command(f'no untagged {port}')
            self.enter_command('exit')
        
        self.enter_command('exit')
        
        return True
    
    @TELNETController.request
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        port_name = self.ports[port]['name']
        
        self.enter_command('configure')
        self.enter_command(f'vlan {vlan}')
        self.enter_command(f'fixed {port}')
        self.enter_command(f'untagged {port}')
        self.enter_command('exit')
        self.enter_command(f'interface {port_name}')
        self.enter_command(f'pvid {vlan}')
        self.enter_command('exit')
        self.enter_command('exit')

        
        return True


class ZYXEL2024_TELNET(ZYXEL2108_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    
    
    @TELNETController.request
    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        self.enter_command('configure')
        for vlan in vlans:
            self.enter_command(f'vlan {vlan}')
            self.enter_command(f'fixed {port}')
            self.enter_command(f'no untagged {port}')
            self.enter_command('exit')
        
        self.enter_command('exit')
        
        return True
    
    @TELNETController.request
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        port_name = self.ports[port]['name']
        
        self.enter_command('configure')
        self.enter_command(f'vlan {vlan}')
        self.enter_command(f'fixed {port}')
        self.enter_command(f'untagged {port}')
        self.enter_command('exit')
        self.enter_command(f'interface {port_name}')
        self.enter_command(f'pvid {vlan}')
        self.enter_command('exit')
        self.enter_command('exit')

        
        return True

class ZYXELMES3528_TELNET(ZYXEL2024_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)

class ZYXELMES3500_24_TELNET(ZYXEL2024_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
        
    @TELNETController.request
    def get_config(self):
        res = ''
        self.connection.write(self.to_bytes('show run'))
        while True:
            index, match, output = self.connection.expect([b"-- more --,", b"#"], timeout=5)
            output = output.decode("utf-8")
            output = re.sub("-- more --, next page: Space, continue: c, quit: ESC", "\n", output)
            res += output
            if index in (1, -1):
                break
            self.connection.write(b" ")
            time.sleep(1)

        return res
    
    @TELNETController.request
    def get_arp_table(self):
        data = self.enter_command("show ip arp")
        data = data.split()
        data = data[11:-1]
        devices = list(zip(*[iter(data)]*6))
        data = []
        for device in devices:
            data.append({
                'ip': device[1],
                'mac': device[2],
                'vlan': device[3],
                'port': device[4]
            })

        return data

class ZYXELMES3500_8_TELNET(ZYXELMES3500_24_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    
    @TELNETController.request
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        port_name = self.ports[port]['name']
        
        self.enter_command('configure')
        self.enter_command(f'vlan {vlan}')
        self.enter_command(f'fixed {port}')
        self.enter_command(f'untagged {port}')
        self.enter_command('exit')
        self.enter_command(f'interface {port_name}')
        self.enter_command(f'pvid {vlan}')
        self.enter_command('exit')
        self.enter_command('exit')

        
        return True

class ZYXELXGS4728_TELNET(ZYXELMES3500_24_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    
    @TELNETController.request
    def get_arp_table(self):
        data = self.enter_command("show ip arp")
        data = data.split()
        data = data[11:-1]
        devices = list(zip(*[iter(data)]*7))
        data = []
        for device in devices:
            data.append({
                'ip': device[1],
                'mac': device[2],
                'vlan': device[3],
                'port': device[4]
            })

        return data

class ZYXELMGS3712_TELNET(ZYXEL2108_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    
    @TELNETController.request
    def get_arp_table(self):
        data = self.enter_command("show ip arp")
        data = data.split()
        data = data[10:-1]
        devices = list(zip(*[iter(data)]*6))
        data = []
        for device in devices:
            
            macs_in_vlan = ''
            self.connection.write(self.to_bytes(f'show mac address-table vlan {device[3]}'))
            while True:
                index, match, output = self.connection.expect([b"-- more --,", b"#"], timeout=5)
                output = output.decode("utf-8")
                output = re.sub("-- more --, next page: Space, continue: c, quit: ESC", "\n", output)
                macs_in_vlan += output
                if index in (1, -1):
                    break
                self.connection.write(b" ")
                time.sleep(1)
    
            macs_in_vlan = macs_in_vlan.split()[11:-1]
            macs_in_vlan = list(zip(*[iter(macs_in_vlan)]*3))
            port = list(filter(lambda x: x[2] == device[2],macs_in_vlan))
            if port:
                port = port[0][0]
            else:
                port = ''

            data.append({
                'ip': device[1],
                'mac': device[2],
                'vlan': device[3],
                'port': port
            })
        return data


class ZYXELGS4012_TELNET(ZYXELMGS3712_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)


class ZYXELIES1248_TELNET(TELNETController):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    
    def to_bytes(self,line):
        return f"{line}\r".encode("utf-8")

    def enter(self):
        self.connection.read_until(b"User name:",timeout=3)
        self.connection.write(self.to_bytes(self.login))
        self.connection.read_until(b"Password:",timeout=3)
        
        for password in self.passwords:
            self.connection.write(self.to_bytes(password))
            index, m, output = self.connection.expect([b"Password:", b">"],timeout=5)
            if index == 1:
                break
        else:
            self.close()
            raise Exception('Incorrect password')

        self.connection.read_until(b">", timeout=3)
        time.sleep(2)
        self.connection.read_very_eager()
    
    def enter_command(self,command):
        self.connection.write(self.to_bytes(command))
        out = self.connection.read_until(b">", timeout=5).decode("utf-8")
        self.res.append(out)
        return out
    
    @TELNETController.request
    def get_config(self):
        res = ''
        self.connection.write(self.to_bytes('config show adsl'))
        while True:
            index, match, output = self.connection.expect([b"press 'e' to exit showall,", b">"], timeout=5)
            output = output.decode("utf-8")
            output = re.sub("press 'e' to exit showall, 'n' for nopause, or any key to continue...", "\n", output)
            res += output
            if index in (1, -1):
                break
            self.connection.write(b" ")
            time.sleep(0.3)

        return res
    
    @TELNETController.request
    def get_arp_table(self):
        data = self.enter_command("ip arp show")
        data = data.split()[8:-1]
        devices = list(zip(*[iter(data)]*2))

        enet1_macs = self.enter_command('statistics mac enet1')
        enet1_macs = enet1_macs.split()
        if len(enet1_macs) > 4:
            enet1_macs = enet1_macs[11:-1]
            enet1_macs = list(zip(*[iter(enet1_macs)]*3))
        else:
            enet1_macs = []

        enet2_macs = self.enter_command('statistics mac enet2')
        enet2_macs = enet2_macs.split()
        if len(enet2_macs) > 4:
            enet2_macs = enet2_macs[11:-1]
            enet2_macs = list(zip(*[iter(enet2_macs)]*3))
        else:
            enet2_macs = []

        data = []
        for device in devices:
            vlan = ''
            port = ''
            find_mac1 = []
            find_mac2 = []

            if enet1_macs:
                find_mac1 = list(filter(lambda x: x[2] == device[1],enet1_macs))
            
            if enet2_macs:
                find_mac2 = list(filter(lambda x: x[2] == device[1],enet2_macs))

            if find_mac1:
                port = 'enet1'
                vlan = find_mac1[0][1]

            if find_mac2:
                port = 'enet2'
                vlan = find_mac2[0][1]

            data.append({
                'ip': device[0],
                'mac': device[1],
                'vlan': vlan,
                'port': port
            })

        return data
    

    @TELNETController.request
    def set_snmp_community(self,community):
        print( self.enter_command(f'sys snmp setcommunity {community}') )
        print( self.enter_command(f'config save') )

        return True