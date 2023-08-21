from pyzabbix import ZabbixAPI

class Zabbix:
    def __init__(self,server,login,password) -> None:
        self.zapi = ZabbixAPI(server)
        self.zapi.login(login,password)
    
    def get_name_by_ip(self,ip):
        data = self.zapi.do_request('hostinterface.get',{ 'filter': {'ip': ip} })['result'][0]
        name = self.zapi.host.get(hostids=data['hostid'])[0]['host']
        return name
    
    def get_items_lastdata_from_ip(self,ip,keys):
        hostid = self.zapi.do_request('hostinterface.get',{ 'filter': {'ip': ip} })['result'][0]['hostid']
        lastdatas = []
        for key in keys:
            lastdatas.append( self.zapi.do_request('item.get',{'filter': {'hostid': hostid, 'key_': key}})['result'][0]['lastvalue'] )
        return lastdatas
    
    def get_devices_from_map(self,map_id):
        result = self.zapi.do_request('map.get',{ 'filter': { 'sysmapid':map_id },'selectSelements': 'extend' })['result'][0]['selements']
        data = []
        for element in result:
            try:
                id = element['selementid']
                label = element['label']
                coordinates = {
                    'x': element['x'],
                    'y': element['y']
                }
                hostid = element['elements'][0]['hostid']

                data.append( (hostid,coordinates,label,id)  )
            except IndexError as e:
                pass
            except KeyError as e:
                pass

        return list(
                map(
                    lambda element:
                        ( 
                            self.zapi.hostinterface.get(hostids=element[0],output=['ip'])[0]['ip'], 
                            self.zapi.host.get(hostids=element[0])[0]['name'],
                            element[1],
                            element[2],
                            element[0],
                            element[3]
                            
                        ), data
                    )
            )
    
if __name__ == '__main__':
    pass