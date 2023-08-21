
from Errors.NetControlExceptions import NoController
from controllers.router.Cisco_router import Cisco2801,Cisco3600

from models.models import Model


def get_controller_routers(model: Model):
    controllers = {
        'Cisco2801': Cisco2801,
        'Cisco3600': Cisco3600
    }
    controller = controllers.get(model.value)
    
    if controller:
        return controller
    else:
        raise NoController("CONTROLLER NOT FINDED")