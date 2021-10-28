from enum import Enum
from typing import List

class Sfp:
    def __init__(self,name,wavelength,speed) -> None:
        self.name = name
        self.wavelength = wavelength
        self.speed = speed

class PortType(Enum):
    FIBER = 'FIBER'
    COOPER = 'COOPER'

class Vlan:
    def __init__(self,id,name) -> None:
        self.id = id
        self.name = name
class Port:
    def __init__( self,num,name,type_port: PortType ) -> None:
        self.num = num
        self.name = name
        self.type_port = type_port
        self.vlans: List[Vlan] = []
    
    def add_vlan(self,vlan: Vlan):
        self.vlans.append(vlan)
    
    def __str__(self) -> str:
        vlans = ' '.join(
                         [ str(i.id) for i in self.vlans ]
                        )
        return f'{self.name} {self.type_port} {vlans}'
        
class Switch:
    def __init__(self,id,name,ip) -> None:
        self.id: int = id
        self.name: str = name
        self.ip: str = ip

class Mes3324f(Switch):
    def __init__(self, id, name, ip) -> None:
        super().__init__(id, name, ip)
        self.ports: List[Port] = [
            Port(1,'Gigabyte1/0/1',PortType.FIBER),
            Port(2,'Gigabyte1/0/2',PortType.FIBER),
            Port(3,'Gigabyte1/0/3',PortType.FIBER),
            Port(4,'Gigabyte1/0/4',PortType.FIBER),
            Port(5,'Gigabyte1/0/5',PortType.FIBER),
            Port(6,'Gigabyte1/0/6',PortType.FIBER),
        ]
    
if __name__ == '__main__':
    sw = Mes3324f(1,'E_B_22.3_0.1','10.3.0.1')
    sw.ports[0].add_vlan(Vlan(301,'msc atc3'))
    for i in sw.ports:
        print(i)
