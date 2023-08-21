from service.Zabbix import Zabbix

import settings

def get_sws_in_zabbix(zabbix_map_id):
    zb = Zabbix(settings.ZABBIX_SERVER,settings.ZABBIX_USERNAME,settings.ZABBIX_PASSWORD)
    zabbix_sws = zb.get_devices_from_map(zabbix_map_id)
    return zabbix_sws