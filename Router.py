from typing import List
from Device import Device
from controllers.router.Router import RouterController
from controllers.router.Controller_routers import get_controller_routers
import models.models as Model
from Errors.NetControlExceptions import NoController


class Router(Device):
    def __init__(self, ip: str, name: str, model: Model.Model, communty: str = None, username: str = None, passwords: list = None, enable: str = None) -> None:
        super().__init__(ip, name, model, communty, username, passwords, enable)
        
        if self.snmp_status:
            self._identify_model()

        self.telnet_data = {
            'ip': self.ip,
            'login': self.username ,
            'passwords': self.passwords,
            'enable' : self.enable
        }
        
        try:
            self.controller: RouterController = get_controller_routers(self.model)(self.snmp,self.telnet_data)
        except NoController as e:
            print(self.ip, e)
            self.controller = None
            
    def _identify_model(self) -> None:
        self.model: Model.Router = Model.get_models_from_description(self.sysdescription)
    
    def _controller_required(method):
        def wrapper(*args, **kwargs):
            self = args[0]
            if self.controller:
                return method(*args, **kwargs)
            else:
                raise NoController("CONTROLLER REQUIRED")
            
        return wrapper
    
    @_controller_required
    def get_allports(self) -> List[tuple]:
        return self.controller.get_allports()
    
    @_controller_required
    def get_mac_from_ip(self,ip) -> str:
        return self.controller.get_mac_from_ip(ip)

if __name__ == '__main__':
    pass