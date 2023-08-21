from pysnmp.hlapi import *
from pysnmp.proto import rfc1902
import time

from typing import List,Tuple

from Errors.NetControlExceptions import SnmpTooBigException

class Snmp:
    def __init__(self,ip: str,community: str):
        self.host: str = ip
        self.community: str = community
        self.port: str = '161'
        
    def walk_base(self,oid):
        temp = []
        for (errorIndication,
                errorStatus,
                errorIndex,
                varBinds) in nextCmd(
                            SnmpEngine(),
                            CommunityData(self.community),
                            UdpTransportTarget( (self.host, self.port) ),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid)),
                            lexicographicMode=False
                            ):

                if errorIndication:
                    print(errorIndication)
                    break
                elif errorStatus:
                    print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                    break
                else:
                    for vals in varBinds:
                        temp.append(vals.prettyPrint())
        
        return temp
    
    def walk_untill_oid_contains(self,oid,value,timeout=2) -> tuple:
        start_time = time.time()
        for (errorIndication,
                errorStatus,
                errorIndex,
                varBinds) in nextCmd(
                            SnmpEngine(),
                            CommunityData(self.community),
                            UdpTransportTarget( (self.host, self.port) ),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid)),
                            lexicographicMode=False
                            ):

                if errorIndication:
                    print(errorIndication)
                    break
                elif errorStatus:
                    print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                    break
                else:
                    for vals in varBinds:
                        d = vals.prettyPrint().split('=')
                        num=d[0].strip()
                        val=d[1].strip()
                        if value in num:
                            return (num,val)
                
                end_time = time.time() - start_time
                if end_time > timeout:
                    return ''
    
    def walk_untill_value_contains(self,oid,value,timeout=10) -> tuple:
        start_time = time.time()
        for (errorIndication,
                errorStatus,
                errorIndex,
                varBinds) in nextCmd(
                            SnmpEngine(),
                            CommunityData(self.community),
                            UdpTransportTarget( (self.host, self.port) ),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid)),
                            lexicographicMode=False
                            ):

                if errorIndication:
                    print(errorIndication)
                    break
                elif errorStatus:
                    print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                    break
                else:
                    for vals in varBinds:
                        d = vals.prettyPrint().split('=')
                        num=d[0].strip()
                        val=d[1].strip()
                        if value in val:
                            return (num,val)
                
                end_time = time.time() - start_time
                if end_time > timeout:
                    return ''
                

    def walk(self,oid) -> List[str]:
        data = []
        temp = self.walk_base(oid)
        if temp:
            for i in temp:
                d = i.split('=')
                val=d[1].strip()
                data.append( val )
                
        return data
    
    def walk_oid_value(self,oid) -> List[tuple]:
        data = []
        temp = self.walk_base(oid)
        if temp:
            for i in temp:
                d = i.split('=')
                num=d[0].strip()
                val=d[1].strip()
                data.append( (num, val) )
        return data
    
    def walk_index(self,oid) -> List[str]:
        data = []
        temp = self.walk_base(oid)
        if temp:
            for i in temp:
                d = i.split('=')
                num=d[0].strip().split('.')[-1]
                data.append(num)
        return data
    
    def walk_index_value(self,oid) -> List[tuple]:
        data = []
        temp = self.walk_base(oid)
        if temp:
            for i in temp:
                d = i.split('=')
                num=d[0].strip().split('.')[-1]
                val=d[1].strip()
                data.append( (num, val) )
        return data
        
    def get(self,oids: list) -> List[Tuple[str,str]]:
        iterator = next(getCmd(
                                    SnmpEngine(),
                                    CommunityData(self.community),
                                    UdpTransportTarget( (self.host, self.port) ),
                                    ContextData(),
                                    *[ObjectType(ObjectIdentity(oid)) for oid in oids])
                        )
        
        errorIndication, errorStatus, errorIndex, varBinds = iterator
        
        if errorIndication:
            raise Exception(errorIndication)

        if errorStatus:
            raise SnmpTooBigException('{} at {}'.format(
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'
            ))

        results = []
        for varBind in varBinds:
            results.append(
                (str(varBind[0]), str(varBind[1]))
                #str(varBind[1])
            )
            
        return results
     
    def set_int(self,oid,value: str):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid),rfc1902.Integer(value),
                                ) ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            raise Exception(str(errorIndication))
        elif errorStatus:
            raise Exception(str(errorStatus))
        else:
            return True
    
    def set_unsigned(self,oid,value: str):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid),rfc1902.Unsigned32(value),
                                ) ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            raise Exception(str(errorIndication))
        elif errorStatus:
            raise Exception(str(errorStatus))
        else:
            return True
    
    def set_string(self,oid,value: str):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid),OctetString(value),) 
                                ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            raise Exception(str(errorIndication))
        elif errorStatus:
            raise Exception(str(errorStatus))
        else:
            return True
    
    def set_hexValue(self,oid,hex_vlan: str):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid),rfc1902.OctetString(hexValue=hex_vlan),
                                ) ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            return (False,errorIndication)
        elif errorStatus:
            return (False,errorStatus)
        else:
            return (True,None)
    
    def set_hexValue_asn(self,oid,hex_vlan: str):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid),OctetString(hexValue=hex_vlan),
                                ) ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            return (False,errorIndication)
        elif errorStatus:
            return (False,errorStatus)
        else:
            return (True,None)
    
    def set_2str_1int(self,oid1,oid2,oid3,value1: str,value2: str,value3: str):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid1),rfc1902.OctetString(value1)),
                                ObjectType(ObjectIdentity(oid2),rfc1902.OctetString(value2)),
                                ObjectType(ObjectIdentity(oid3),rfc1902.Integer(value3)), 
                                ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            return (False,errorIndication)
        elif errorStatus:
            return (False,errorStatus)
        else:
            return (True,None)
    
    def set_hexValue_2oid(self,oid1,oid2,hex_vlan: str):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid1),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid2),rfc1902.OctetString(hexValue=hex_vlan)) 
                                ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            return (False,errorIndication)
        elif errorStatus:
            return (False,errorStatus)
        else:
            return (True,None)
    
    def set_hexValue_4oid(self,oid1,oid2,fill_null,hex_vlan):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid1),rfc1902.OctetString(hexValue=fill_null)),
                                ObjectType(ObjectIdentity(oid2),rfc1902.OctetString(hexValue=fill_null)),
                                ObjectType(ObjectIdentity(oid1),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid2),rfc1902.OctetString(hexValue=hex_vlan)) 
                                ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            return (False,errorIndication)
        elif errorStatus:
            return (False,errorStatus)
        else:
            return (True,None)
    
    def set_hexValue_8oid(self,oid1,oid2,oid3,oid4,oid5,oid6,oid7,oid8,hex_vlan):
        iterator = next(setCmd(
                                SnmpEngine(),
                                CommunityData(self.community),
                                UdpTransportTarget( (self.host, self.port) ),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid1),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid2),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid3),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid4),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid5),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid6),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid7),rfc1902.OctetString(hexValue=hex_vlan)),
                                ObjectType(ObjectIdentity(oid8),rfc1902.OctetString(hexValue=hex_vlan)) 
                                ),
        )

        errorIndication, errorStatus, errorIndex, vals = iterator
        if errorIndication:
            return (False,errorIndication)
        elif errorStatus:
            return (False,errorStatus)
        else:
            return (True,None)

if __name__ == '__main__':
    pass
        
