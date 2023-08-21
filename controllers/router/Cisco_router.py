from typing import Dict
from controllers.router.Router import RouterController
from service.Snmp import Snmp


class Cisco2801(RouterController):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)

class Cisco3600(RouterController):
    def __init__(self, snmp_con: Snmp, telnet_data: Dict) -> None:
        super().__init__(snmp_con, telnet_data)