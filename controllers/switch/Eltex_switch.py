from typing import List
from controllers.switch.Switch import SwitchController, TELNETController
from service.Snmp import Snmp

import time

class MES3324(SwitchController):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                            [ ( str(i), {'index': str(i+48),'name' : f'gi1/0/{i}' } ) for i in range(1,25) ] +
                            [ ( str(i), {'index': str(i+80),'name' : f'te1/0/{i - 24}' } ) for i in range(25,29) ] +
                            [ ( str(i), {'index': str(i+971),'name' : f'Po{str(i - 28)}' } ) for i in range(29,34) ] 
                    )
        self.telnet_con = MES3324_TELNET(self.ports,**telnet_data)
    
    def get_arp_table(self) -> List[dict]:
        return self.telnet_con.get_arp_table()
    
    def get_switchport_mode_on_port(self,port: str) -> str:
        return self.telnet_con.get_switchport_mode_on_port(port)
    
    def get_switchport_mode_on_all_ports(self) -> dict:
        return self.telnet_con.get_switchport_mode_on_all_ports()
    
    def get_vlans_on_port(self,port) -> List[str]:
        return self.get_trunk_vlans_on_port(port)
    
    def get_access_vlan_on_port(self,port) -> List[str]:
        return self.get_trunk_vlans_on_port(port)
    
    def get_vlans_on_all_ports(self) -> List[List[str]]:
        return self.get_trunk_vlans_on_all_ports()
    
    def get_ports_on_vlan(self,vlan) -> List[str]:
        vlan = vlan.strip()
        d = self.snmp_con.get([f'1.3.6.1.2.1.17.7.1.4.3.1.2.{vlan}'])[0][1]
        return list(
                map(lambda x:
                        [ i for i in self.ports if self.ports[i]['index'] == x ][0]
                    ,
                    self._get_dec_vlans( self._convert_to_hex(d),0 )
                )
        )
        
    def get_trunk_vlans_on_port(self,port :str) -> List[str]:
        if not self.ports.get(port):
            raise Exception('Port not find')

        index = self.ports[port]['index']
        vlans = []
        for i in range(1,5):
            data = self.snmp_con.get([f'1.3.6.1.4.1.89.48.68.1.{i}.{index}'])
            if data:
                data = data[0]
                val = data[1]
                vlans += self._get_dec_vlans( self._convert_to_hex(val),1024*(i-1) )
            
        return vlans
    
    def get_trunk_vlans_on_all_ports(self) -> List[List[str]]:
        res = []
        for port in self.ports:
            if not self.ports.get(port):
                raise Exception('Port not find')

            index = self.ports[port]['index']
            vlans = []
            for i in range(1,5):
                data = self.snmp_con.get([f'1.3.6.1.4.1.89.48.68.1.{i}.{index}'])
                if data:
                    data = data[0]
                    val = data[1]
                    vlans += self._get_dec_vlans( self._convert_to_hex(val),1024*(i-1) )
                
            res.append( vlans )
        
        return res
        
    #check
    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')

        port = self.ports[port]['index']
        many_vlans = self._distribute_vlans(vlans)
        results = []
        for n,vlans_data_table_i in enumerate(many_vlans):
          if vlans_data_table_i:
            created = self.create_vlan(vlans_data_table_i,(n+2))
            if created:
              exists_vlans_on_port = self._convert_to_hex(self.snmp_con.get([f'1.3.6.1.4.1.89.48.68.1.{n+1}.{port}'])[0][1])
              bin_vlans = self._convert_hex_to_bin(exists_vlans_on_port)
              new_bin_vlans = self._add_to_place(vlans_data_table_i,bin_vlans,(n+2),'1')
              new_hex_vlans = self._convert_bin_to_hex(new_bin_vlans)
              if new_hex_vlans:
                try:
                    res = self.snmp_con.set_hexValue(f'1.3.6.1.4.1.89.48.68.1.{n+1}.{port}',new_hex_vlans)
                    results.append(True)
                except Exception as e:
                    print(self.snmp_con.host,e)
                    results.append(False)
                    
        if all(results):
            return True
        else:
            return False
        
    #check
    def delete_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')

        port = self.ports[port]['index']
        many_vlans = self._distribute_vlans(vlans)
        results = []
        for n,vlans_data_table_i in enumerate(many_vlans):
          if vlans_data_table_i:
              bin_ex_vlans = self.snmp_con.get([f'1.3.6.1.4.1.89.48.68.1.{n+1}.{port}'])[0][1] #TODO
              exists_vlans_on_port = self._convert_to_hex(bin_ex_vlans)
              bin_vlans = self._convert_hex_to_bin(exists_vlans_on_port)
              new_bin_vlans = self._add_to_place(vlans_data_table_i,bin_vlans,(n+2),'0')
              new_hex_vlans = self._convert_bin_to_hex(new_bin_vlans)
              if new_hex_vlans:
                try:
                    res = self.snmp_con.set_hexValue(f'1.3.6.1.4.1.89.48.68.1.{n+1}.{port}',new_hex_vlans)
                    results.append(True)
                except Exception as e:
                    print(self.snmp_con.host,e)
                    results.append(False)
              else:
                results.append(False)
        
        if all(results):
            return True
        else:
            return False

    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        if not self.ports.get(port):
            raise Exception('Port not find')

        port = self.ports[port]['index']
        data = {
            'num':0,
            'oid':''
        }
        int_dec_vlan = int(vlan)
        
        if int_dec_vlan <= 1024:
            data['num'] = 0
            data['oid1'] = f'1.3.6.1.4.1.89.48.68.1.1.{port}'
            data['oid2'] = f'1.3.6.1.4.1.89.48.68.1.5.{port}'
        elif int_dec_vlan <= 2048:
            data['num'] = 1
            data['oid1'] = f'1.3.6.1.4.1.89.48.68.1.2.{port}'  
            data['oid2'] = f'1.3.6.1.4.1.89.48.68.1.6.{port}'
        elif int_dec_vlan <= 3072:
            data['num'] = 2
            data['oid1'] = f'1.3.6.1.4.1.89.48.68.1.3.{port}'
            data['oid2'] = f'1.3.6.1.4.1.89.48.68.1.7.{port}'
        elif int_dec_vlan <= 4095:
            data['num'] = 3
            data['oid1'] = f'1.3.6.1.4.1.89.48.68.1.4.{port}'
            data['oid2'] = f'1.3.6.1.4.1.89.48.68.1.8.{port}'

        created = self.create_vlan([vlan],(data['num'] + 2))
        if created:
            self._delete_all_vlans(port)
            fill_nulls_bin = '0'*1024
            bin_vlans = fill_nulls_bin 
            new_bin_vlans = self._add_to_place([vlan],bin_vlans,data['num']+2,'1')
            new_hex_vlans = self._convert_bin_to_hex(new_bin_vlans)
            if new_hex_vlans:
                try:
                    res = self.snmp_con.set_hexValue_2oid(data['oid1'],data['oid2'],new_hex_vlans)
                except Exception as e:
                    print(self.snmp_con.host,e)
                    return False
                return True
        
        return False
                   
    #check
    def create_vlan(self,vlans: List[str],num) -> bool:
        exists_vlans = self._convert_to_hex( self.snmp_con.get([f'1.3.6.1.4.1.89.48.69.1.{num}.0'])[0][1] ) #TODO
        bin_vlans = self._convert_hex_to_bin(exists_vlans)
        new_bin_vlans = self._add_to_place(vlans,bin_vlans,num,'1')
        new_hex_vlans = self._convert_bin_to_hex(new_bin_vlans)
        try:
            result = self.snmp_con.set_hexValue(f'1.3.6.1.4.1.89.48.69.1.{num}.0',new_hex_vlans)
        except Exception as e:
            print(self.snmp_con.host, e)
            return False
        
        return True
    
    
    def _add_to_place(self,vlans,bin_vlans,num,value):   
      for vlan in vlans:      
         if num == 2:
            bin_vlans = bin_vlans[:(int(vlan)-1)] + value + bin_vlans[(int(vlan)-1) + 1:]
         elif num == 3:
            bin_vlans = bin_vlans[:(int(vlan)-1-1024)] + value + bin_vlans[(int(vlan)-1-1024) + 1:]
         elif num == 4:
            bin_vlans = bin_vlans[:(int(vlan)-1-2048)] + value + bin_vlans[(int(vlan)-1-2048) + 1:]
         elif num == 5:
            bin_vlans = bin_vlans[:(int(vlan)-1-3072)] + value + bin_vlans[(int(vlan)-1-3072) + 1:]
        
      return bin_vlans
  
    def _distribute_vlans(self,vlans):
        vlans_data_table_one = []
        vlans_data_table_two = []
        vlans_data_table_three = []
        vlans_data_table_four = []
        for vlan in vlans:
           int_dec_vlan = int(vlan)
           if int_dec_vlan <= 1024:
             vlans_data_table_one.append(vlan)
           elif int_dec_vlan <= 2048:
             vlans_data_table_two.append(vlan)
           elif int_dec_vlan <= 3072:
             vlans_data_table_three.append(vlan)
           elif int_dec_vlan <= 4095:
             vlans_data_table_four.append(vlan)
        
        many_vlans = [vlans_data_table_one,vlans_data_table_two,vlans_data_table_three,vlans_data_table_four]
        
        return many_vlans
  
    def _get_dec_vlans(self,hex_vlans,num: int):
        vlans = []
        it = 0
        for hex_num in hex_vlans:
            if hex_num == '0':
                it += 1
            else:
                n_bin = bin(int(hex_num, 16))[2:].zfill(4)
                for i in range(len(n_bin)):
                    if n_bin[i] == '1':
                        vlans.append( str( 4*it + i+1 + num) )
                it +=1
        return vlans
    
    def _delete_all_vlans(self,port):
        oids = []
        for i in range(1,8+1):
            oids.append(f'1.3.6.1.4.1.89.48.68.1.{i}.{port}')
        
        try:
            res = self.snmp_con.set_hexValue_8oid(oids[0],oids[1],oids[2],oids[3],oids[4],oids[5],oids[6],oids[7],'0'*256)
        except Exception as e:
            print(self.snmp_con.host,e)
            raise Exception(f"Error delete vlans on {port} port")
        
        return True

class MES3124(MES3324):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.telnet_con = MES3124_TELNET(self.ports,**telnet_data)

class MES2324(MES3324):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
  
class MES5324(MES3324):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                            [ ( str(i), {'index': str(i),'name' : f'te1/0/{i}' } ) for i in range(1,25) ] +
                            [ ( '25',   {'index': '27','name' : f'fo1/0/3' } ), ( '26',   { 'index': '28','name' : f'fo1/0/4' } ) ] + 
                            [ ( '27',   {'index': '49','name' : f'gi1/0/1' } ) ] +
                            [ ( str(i), { 'index': str(i+25),'name' : f'te2/0/{i - 27}' } ) for i in range(28,52) ] +
                            [ ( '52',   {'index': '79','name' : f'fo2/0/3' } ), ( '53',   {'index': '80','name' : f'fo2/0/4' } ) ] + 
                            [ ( '54',  {'index': '101','name' : f'gi2/0/1' } ) ] +
                            [ ( str(i), {'index': str(i+945),'name' : f'Po{i - 54}' } ) for i in range(55,103) ] 
                    )
        
        self.telnet_con = MES5324_TELNET(self.ports, **telnet_data)

class MES5316(MES3324):
    def __init__(self, snmp_con: Snmp, telnet_data: dict) -> None:
        super().__init__(snmp_con, telnet_data)
        self.ports = dict( 
                            [ ( str(i), {'index': str(i),'name' : f'te1/0/{i}' } ) for i in range(1,17) ] +
                            [ ( str(i), {'index': str(i+983),'name' : f'Po{i-16}' } ) for i in range(17,27) ]
                    )
        self.telnet_con = MES5316_TELNET(self.ports, **telnet_data)
        
        
class MES3324_TELNET(TELNETController):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
        
    def enter(self):
        self.connection.read_until(b"User Name:",timeout=3)
        self.connection.write(self.to_bytes(self.login))
        self.connection.read_until(b"Password:",timeout=3)

        #TODO retry enter password
        for password in self.passwords:
            self.connection.write(self.to_bytes(password))
            index, m, output = self.connection.expect([b"Password:", b"#"],timeout=5)
            if index == 1:
                break
            elif index == -1:
                self.connection.write(self.to_bytes(' '))
                self.connection.read_until(b"User Name:",timeout=5)
                self.connection.write(self.to_bytes(self.login))
                self.connection.read_until(b"Password:",timeout=5)
        else:
            self.close()
            raise Exception('Incorrect password')
        
        index, m, output = self.connection.expect([b">", b"#"],timeout=3)
        if index == 0:
            self.connection.write(b"enable\n")
            self.connection.read_until(b"Password:")
            self.connection.write(self.to_bytes(self.enable))
            self.connection.read_until(b"#", timeout=3)
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
    def get_arp_table(self):
        data = self.enter_command("show arp")
        data = data.split()
        data = data[18:-1]
        devices = list(zip(*[iter(data)]*6))
        data = []
        for device in devices:
            port = ''
            find_port = list(filter(lambda port: device[2] == self.ports[port]['name'],self.ports))
            if find_port:
                port = find_port[0]

            res = {
                'ip': device[3],
                'mac': device[4],
                'vlan': device[1],
                'port': port
            }
            
            data.append(res)

        return data
    
    @TELNETController.request
    def get_switchport_mode_on_port(self,port: str) -> str:
        port_name = self.ports[port]['name']
        data = self.enter_command(f"show run int {port_name}")
        data = list(map( lambda x: x.replace('\r',''), data.split('\n') ) )
        data = list(filter(lambda x: 'switchport' in x,data))
        if data:
            data = ''.join(data)
            
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
            data = list(map( lambda x: x.replace('\r',''), data.split('\n') ) )
            data = list(filter(lambda x: 'switchport' in x,data))
            
            if data:
                data = ''.join(data)
                
                if 'trunk' in data:
                    res[port] = 'trunk'
                elif 'access' in data:
                    res[port] = 'access'
                else:
                    res[port] = 'unknown'
            else:
                res[port] = 'unknown'
        
        return res


class MES3124_TELNET(MES3324_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    
    @TELNETController.request
    def get_arp_table(self):
        data = self.enter_command("show arp")
        data = data.split()
        data = data[13:-1]
        devices = list(zip(*[iter(data)]*6))
        data = []
        for device in devices:
            port = ''
            find_port = list(filter(lambda x: device[2] == x[0],self.ports))
            if find_port:
                port = find_port[0][1]

            data.append({
                'ip': device[3],
                'mac': device[4],
                'vlan': device[1],
                'port': port
            })

        return data

class MES5324_TELNET(MES3324_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)

class MES5316_TELNET(MES3324_TELNET):
    def __init__(self, ports: list, ip, login, passwords, enable) -> None:
        super().__init__(ports, ip, login, passwords, enable)
    
    
    @TELNETController.request
    def get_arp_table(self):
        data = self.enter_command("show arp")
        data = data.split()[22:-1]
        devices = list(zip(*[iter(data)]*6))
        data = []
        for device in devices:
            port = ''
            find_port = list(filter(lambda x: device[2] == x[0],self.ports))
            if find_port:
                port = find_port[0][1]

            data.append({
                'ip': device[3],
                'mac': device[4],
                'vlan': device[1],
                'port': port
            })

        return data