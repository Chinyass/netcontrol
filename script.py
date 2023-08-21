from scripts.topology import get_sws_in_zabbix


if __name__ == '__main__':
    data = get_sws_in_zabbix('36')
    print(list(filter( lambda x: x[0] in ['10.254.22.36','10.9.1.13','10.9.1.2'],data)))