
from Errors.NetControlExceptions import NoController
from controllers.switch.Qtech_switch import (
    QSW2850_28,
    QSW2850_10,
    QSW2800_28,
    QSW2910_26,
    QSW2910_28,
    QSW3470_28,
    QSW4610_10,
    QSW4610_28
)

from controllers.switch.Eltex_switch import(
    MES3324,
    MES2324,
    MES3124,
    MES5316,
    MES5324,
    
)
from controllers.switch.Zyxel_switch import(
    ZYXEL2108,
    ZYXEL2024,
    ZYXELMES3528,
    ZYXELMES3500_24,
    ZYXELMES3500_8,
    ZYXELXGS4728,
    ZYXELMGS3712,
    ZYXELGS4012,
    ZYXELIES1248
)
from models.models import Model


def get_controller_switch(model: Model):
    controllers = {
        'QSW2850_28': QSW2850_28,
        'QSW2850_10': QSW2850_10,
        'QSW2800_28': QSW2800_28,
        'QSW2910_26': QSW2910_26,
        'QSW2910_28': QSW2910_28,
        'QSW3470_28': QSW3470_28,
        'QSW4610_10': QSW4610_10,
        'QSW4610_28': QSW4610_28,
        
        'MES3324': MES3324,
        'MES2324': MES2324,
        'MES3124': MES3124,
        'MES5316': MES5316,
        'MES5324': MES5324,
        
        'ZYXEL2108': ZYXEL2108,
        'ZYXEL2024': ZYXEL2024,
        'ZYXELMES3528': ZYXELMES3528,
        'ZYXELMES3500_24': ZYXELMES3500_24,
        'ZYXELMES3500_8': ZYXELMES3500_8,
        'ZYXELXGS4728': ZYXELXGS4728,
        'ZYXELMGS3712': ZYXELMGS3712,
        'ZYXELGS4012': ZYXELGS4012,
        'ZYXELIES1248': ZYXELIES1248
    }
    
    controller = controllers.get(model.value)
    
    if controller:
        return controller
    else:
        raise NoController("CONTROLLER NOT FINDED")