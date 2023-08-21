import time
from typing import Dict, List
from Device import Device
from Errors.NetControlExceptions import NoController
from controllers.switch.Controller_switchs import get_controller_switch
from controllers.switch.Switch import SwitchController
import models.models as Model

import settings

class Switch(Device):
    def __init__(self, ip: str, name: str, model: Model.Switch, communty: str = None, username: str = None, passwords: list = None, enable: str = None) -> None:
        super().__init__(ip, name, model, communty, username, passwords, enable)
        
        if self.snmp_status:
            self._identify_model()
        
        self.telnet_data = {
            'ip': self.ip,
            'login': self.username,
            'passwords': self.passwords,
            'enable' : self.enable
        }
        
        try:
            self.controller: SwitchController = get_controller_switch(self.model)(self.snmp,self.telnet_data)
        except NoController as e:
            print(self.ip, e)
            self.controller = None
            
    def _identify_model(self) -> None:
        self.model: Model.Switch = Model.get_models_from_description(self.sysdescription)

    def _controller_required(method):
        def wrapper(*args, **kwargs):
            self = args[0]
            if self.controller:
                return method(*args, **kwargs)
            else:
                raise NoController("CONTROLLER REQUIRED")
            
        return wrapper
    
    @_controller_required
    def get_ifname(self,port: str) -> str:
        return self.controller.get_ifname(port)
    
    @_controller_required
    def get_ports(self) -> Dict[str,Dict[str,str]]:
        return self.controller.get_ports()
    
    @_controller_required
    def get_port_status(self,port: str) -> bool:
        return self.controller.get_port_status(port)
    
    @_controller_required
    def get_all_info_ports(self) -> List[Dict]:
        return self.controller.get_all_info_ports()
    
    @_controller_required
    def get_self_mac(self) -> str:
        return self.controller.get_self_mac()
    
    @_controller_required
    def get_port_from_mac(self,hexmac: str) -> str:
        return self.controller.get_port_from_mac(hexmac)
    
    @_controller_required
    def get_vlans_on_port(self,port: str) -> List[str]:
        return self.controller.get_vlans_on_port( port )

    @_controller_required
    def get_ports_on_vlan(self,vlan) -> List[str]:
        return self.controller.get_ports_on_vlan(vlan)
    
    @_controller_required
    def get_access_vlan_on_port(self,port) -> List['str']:
        return self.controller.get_access_vlan_on_port(port)
    
    @_controller_required
    def set_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        return self.controller.set_trunk_vlans_on_port(port,vlans)
    
    @_controller_required
    def delete_trunk_vlans_on_port(self,port: str, vlans: List[str]) -> bool:
        return self.controller.delete_trunk_vlans_on_port(port,vlans)
    
    @_controller_required
    def set_access_vlan_on_port(self,port: str, vlan: str) -> bool:
        return self.controller.set_access_vlan_on_port(port,vlan)
    
    @_controller_required
    def get_arp_table(self) -> List[dict]:
        return self.controller.get_arp_table()
    
    @_controller_required
    def get_switchport_mode_on_port(self,port: str) -> str:
        return self.controller.get_switchport_mode_on_port(port)
    
    @_controller_required
    def get_switchport_mode_on_all_ports(self) -> dict:
        return self.controller.get_switchport_mode_on_all_ports()
    
    @_controller_required
    def get_mac_gateway(self) ->str:
        return self.controller.get_mac_gateway()
    
    @_controller_required
    def get_uplink_port(self) -> str:
        return self.controller.get_uplink_port()
    

if __name__ == '__main__':
    ip = '10.3.0.27'
    name = 'unknown'
    model = Model.Model.UNKNOWN
    community = settings.RW_COMMUNITY
    username = settings.USERNAME
    passwords: List[str] = settings.PASSWORDS
    enable = settings.ENABLE
    
    a = Switch(ip,name,model,community,username,passwords,enable)
    
    print("PING:",a.ping)
    print("MODEL: ",a.model)
    
    print('IFNAME: ',a.get_ifname('1'))
    print('PORT status: ',a.get_port_status('1'))
    print('VLANS ON PORT ',a.get_vlans_on_port('12'))
    print('ACCESS VLANS ON PORT 1',a.get_access_vlan_on_port('1'))
    print('PORTS ON VLAN ',a.get_ports_on_vlan('2202'))
    print('SELF MAC: ',a.get_self_mac())
    print('PORT FROM MAC',a.get_port_from_mac('a8:f9:4b:fd:c7:49'))
    print('INFO: ',a.get_all_info_ports())
    print('MAC GATEWAY',a.get_mac_gateway())
    print('UPLINK PORT: ',a.get_uplink_port())
    '''
    
    '''
    #print('VLANS ON PORT ',a.get_vlans_on_port('49'))
    #print('SET TRUNK VLANS 11',a.set_trunk_vlans_on_port('49',['3774','3776']))
    #print('VLANS ON PORT ',a.get_vlans_on_port('49'))
    #print('VLANS ON PORT ',a.get_vlans_on_port('1'))
    #print('SET ACCESS VLAN',a.set_access_vlan_on_port('1','3888'))
    #print('VLANS ON PORT ',a.get_vlans_on_port('1'))
    
    #print('ARP TABLE',a.get_arp_table())
    #time.sleep(2)
    #print('SWITCHPORT MODE 1',a.get_switchport_mode_on_port('1'))
    #time.sleep(2)
    #print('SWITCHPORT ALL: ',a.get_switchport_mode_on_all_ports())
    
    #print("DELETE TRUNK VLANS ",a.delete_trunk_vlans_on_port('9',['3888','3999']))