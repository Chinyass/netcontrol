from enum import Enum

class Model(Enum):
    UNKNOWN: str = 'UNKNOWN'
    
class Switch(Enum):
    MES3324: str = 'MES3324'
    MES3124: str = 'MES3124'
    MES2324: str = 'MES2324'
    MES5324: str = 'MES5324'
    MES5316: str = 'MES5316'
    QSW2850_28: str = 'QSW2850_28'
    QSW2850_10: str = 'QSW2850_10'
    QSW2800_28: str = 'QSW2800_28'
    QSW2910_26: str = 'QSW2910_26'
    QSW2910_28: str = 'QSW2910_28'
    QSW3470_28: str = 'QSW3470_28'
    QSW4610_10: str = 'QSW4610_10'
    QSW4610_28: str = 'QSW4610_28'
    ZYXEL2108: str = 'ZYXEL2108'
    ZYXEL2024: str = 'ZYXEL2024'
    ZYXELMES3528: str = 'ZYXELMES3528'
    ZYXELMES3500_24: str = 'ZYXELMES3500_24'
    ZYXELMES3500_8: str = 'ZYXELMES3500_8'
    ZYXELXGS4728: str = 'ZYXELXGS4728'
    ZYXELMGS3712: str = 'ZYXELMGS3712'
    ZYXELGS4012: str = 'ZYXELGS4012'
    ZYXELIES1248: str = 'ZYXELIES1248'

class Router(Enum):
    Cisco2801: str = 'Cisco2801'
    Cisco3600: str = 'Cisco3600'

def get_models_from_description(descr: str) -> Model:
    if not descr:
            return Model.UNKNOWN
        
    if 'MES3324' in descr:
        return Switch.MES3324
    elif 'MES3124' in descr:
        return Switch.MES3124
    elif 'MES2324' in descr:
        return Switch.MES2324
    elif 'MES5324' in descr:
        return Switch.MES5324
    elif 'MES5316' in descr:
        return Switch.MES5316
    
    elif 'Cisco IOS Software, 2801' in descr:
        return Router.Cisco2801
    elif '3600 Software' in descr:
        return Router.Cisco3600
        
    elif descr == 'QTECH':
        return Switch.QSW2910_26
    elif 'QSW-2910-28' in descr:
        return Switch.QSW2910_28
    elif 'QSW-2850-10' in descr:
        return Switch.QSW2850_10
    elif 'QSW-2850-28' in descr:
        return Switch.QSW2850_28
    elif 'QSW-2800-28' in descr:
        return Switch.QSW2800_28
    elif 'QSW-3470-28' in descr:
        return Switch.QSW3470_28
    elif 'QSW-4610-28' in descr:
        return Switch.QSW4610_28
    elif 'QSW-4610-10' in descr:
        return Switch.QSW4610_10
    
    elif 'ES-2108' in descr:
        return Switch.ZYXEL2108
    elif 'ES-2024' in descr:
        return Switch.ZYXEL2024
    elif 'MES-3528' in descr:
        return Switch.ZYXELMES3528
    elif 'MES3500-24' in descr:
        return Switch.ZYXELMES3500_24
    elif 'ES3500-8' in descr:
        return Switch.ZYXELMES3500_8
    elif 'ES-2108' in descr:
        return 'Zyxel2108'
    elif 'XGS-4728' in descr:
        return Switch.ZYXELXGS4728
    elif 'MGS-3712' in descr:
        return Switch.ZYXELMGS3712
    elif 'GS-4012F' in descr:
        return Switch.ZYXELGS4012
    elif 'IES1248' in descr:
        return Switch.ZYXELIES1248
    
    else:
        return Model.UNKNOWN
    '''
    elif '3600 Software' in descr:
        return 'CiscoRouter3600'
    elif 'Cisco IOS Software, 2801' in descr:
        return 'CiscoRouter2801'
    elif 'Cisco IOS Software, C3560E' in descr:
        return 'Cisco3560'
    elif 'Cisco IOS Software, C2960' in descr:
        return 'Cisco2960'
    elif 'Catalyst 4500' in descr:
        return 'Cisco4500'
    elif 'C2960' in descr:
        return 'CiscoC2960'
    elif 'C2950' in descr:
        return 'CiscoC2950'
    elif descr == '24-Port 10/100Mbps + 4-Port Gigabit L2 Managed Switch':
        return 'TPLINK5428'
    
    elif 'IES1248' in descr:
        return 'ZyxelIES1248'
    elif 'ES-2108' in descr:
        return 'Zyxel2108'
    elif 'GS-4012F' in descr:
        return 'ZyxelGS4012'
    elif 'XGS-4728F' in descr:
        return 'ZyxelXGS4728'
    elif 'MGS-3712F' in descr:
        return 'ZyxelMGS3712'
    elif 'ES-2024' in descr:
        return 'Zyxel2024'
    elif 'ES3500-8' in descr:
        return 'Zyxel3500_8'
    elif 'MES-3528' in descr:
        return 'ZyxelMES3528'
    elif 'MES3500-24' in descr:
        return 'ZyxelMES3500_24'
    elif '2148DC' in descr:
        return 'DSLAM2148DC'
    elif 'QTECH EPON' in descr:
        return 'QTECHQSW9001'
    elif 'AAM1212-51' in descr:
        return 'ZyxelIES1000'
    elif 'ME360x' in descr:
        return 'ME360x'
    elif 'Linux' in descr:
        return 'Linux'
    else:
        raise Exception("Model not found")
    '''