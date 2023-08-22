from collections import Counter
from typing import List
from service.Zabbix import Zabbix
import settings

from Switch import Switch
import models.models as Model
import concurrent.futures


def get_sws_in_zabbix(zabbix_map_id):
    zb = Zabbix(settings.ZABBIX_SERVER,settings.ZABBIX_USERNAME,settings.ZABBIX_PASSWORD)
    zabbix_sws = zb.get_devices_from_map(zabbix_map_id)
    sws = []
    for zb_sw in zabbix_sws:
        sw = Switch( 
                zb_sw[0], 
                zb_sw[1], 
                Model.Model.UNKNOWN,
                settings.RO_COMMUNITY,
                settings.USERNAME,
                settings.PASSWORDS,
                settings.ENABLE
            ) 
        sw.coordinates = zb_sw[2]
        sw.label = zb_sw[3]

        sws.append(sw)
        
    sws = filter_sws(sws)
    active_sws = sws['active']
    correct_sws = filter_correct_data(active_sws)['active']
    create_topology(correct_sws)

    format_to_node_ver(correct_sws)
    print('OFFLINE',sws['offline'])
    print('NO_SNMP:',sws['no_snmp'])

    return correct_sws



def filter_sws(sws: Switch):
    return {
        'active': list(filter(lambda x: x.ping and x.snmp_status and x.model != Model.Model.UNKNOWN,sws)),
        'offline': list(filter(lambda x: not x.ping,sws)),
        'no_snmp': list(filter(lambda x: x.ping and not x.snmp_status,sws))
    }

def update_data_on_sw(sw: Switch):
    try:
        mac = sw.get_self_mac_from_arp_router()
        uplink = sw.get_uplink_port()
        if all([mac,uplink]):
            sw.mac = mac
            sw.uplink = uplink
            sw.not_error = True
        else:
            print(sw.ip, sw.model ,'MAC',sw.mac,'UPLINK',sw.uplink)
            sw.not_error = False
    except Exception as e:
        print(sw.ip, sw.model ,'MAC',sw.mac,'UPLINK',sw.uplink, e)
        sw.not_error = False

def filter_correct_data(sws: Switch):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for sw in sws:
            futures.append( executor.submit(update_data_on_sw, sw) )
        for future in concurrent.futures.as_completed(futures):
            results.append( future.result() )
    
    active_sws = list(filter(lambda x: x.not_error,sws))
    failed_sws = list(filter(lambda x: not x.not_error,sws))

    return {
        'active': active_sws,
        'failed': failed_sws
    }

def find_connections(that_sw,data):
    exlude_data = list(filter(lambda x: x != that_sw,data))
    that_ports = that_sw.get_ports()
    for another_sw in exlude_data:
        port = that_sw.get_port_from_mac(another_sw.mac)
        if port and port != that_sw.uplink and port != '0':
            that_port = list(filter(lambda x: that_ports[x]['index'] == port,that_ports))
            if that_port:
                that_port = that_port[0]
                that_sw.connections.append((that_port,another_sw))
            else:
                raise Exception("Error not find port")
    that_uplink = list(filter(lambda x: that_ports[x]['index'] == that_sw.uplink,that_ports))
    if that_uplink:
        that_uplink = that_uplink[0]
        that_sw.uplink = that_uplink

def create_topology(data):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for that_sw in data:
            futures.append( executor.submit(find_connections, that_sw, data) )
        for future in concurrent.futures.as_completed(futures):
            results.append( future.result() )

def format_to_node_ver(data : List[Switch]):
    for sw in data:
        new_connections = []
        count_repeart_ports = Counter(map(lambda x: x[0],sw.connections))
     
        repeat_ports = filter(lambda x: count_repeart_ports[x] > 1,count_repeart_ports)
       
        repeat_ports = list(map(lambda x: x ,repeat_ports))

        not_repeat_ports = filter(lambda x: count_repeart_ports[x] == 1,count_repeart_ports)
        
        not_repeat_ports = list(map(lambda x: x ,not_repeat_ports))
        
        upper_sw = None
        for repeat_port in repeat_ports:
            try:
                repeat_sws = list(filter(lambda x: x[0] == repeat_port,sw.connections))
                repeat_sws = list(map(lambda x: x[1],repeat_sws))
                for repeat_sw in repeat_sws:
                    near_sws = list(filter(lambda x: repeat_sw != x,repeat_sws))
                    sws_in_repeat_sws = list(map(lambda x: x[1],repeat_sw.connections))
                    
                    if sws_in_repeat_sws == near_sws:
                        upper_sw = repeat_sw
                        upper_sw.parent = sw
                        break
                    
                new_connections.append( ({'target': upper_sw.ip, 'on_port': repeat_port, 'to_port': upper_sw.uplink},upper_sw) ) # 2nd need for set_layer_loop
            
            except Exception as e:
                print(f"NOT FOUND connected switch {sw.ip} to {repeat_port}")

            
        
        for not_repeat_port in not_repeat_ports:
            not_repeat_sw = list(filter(lambda x: x[0] == not_repeat_port,sw.connections))[0][1]
            new_connections.append( ({'target': not_repeat_sw.ip, 'on_port': not_repeat_port, 'to_port': not_repeat_sw.uplink},not_repeat_sw) )
            not_repeat_sw.parent = sw
        
        sw.connections_new = new_connections
    
    for sw in data:
        sw.connections = sw.connections_new