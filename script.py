from typing import List
from Switch import Switch
from scripts.topology import get_sws_in_zabbix


if __name__ == '__main__':
    data: List[Switch] = get_sws_in_zabbix('36')
    for sw in data:
        print(sw.ip,sw.model)
        print(' ping: ',sw.ping)
        print(' SNMP: ', sw.snmp_status)
        print(sw.mac)
        print(sw.uplink)
        print(sw.connections)
        print(sw.coordinates)
        