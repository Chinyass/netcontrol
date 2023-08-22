import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

RO_COMMUNITY = os.getenv('RO_COMMUNITY')
RW_COMMUNITY = os.getenv("RW_COMMUNITY")
USERNAME = os.getenv("USERNAME1")
PASSWORDS = os.getenv("PASSWORDS").split(',')
ENABLE = os.getenv("ENABLE")
USERNAME_GATEWAY= os.getenv("USERNAME_GATEWAY")
PASSWORD_GATEWAY= os.getenv("PASSWORD_GATEWAY")
ENABLE_GATEWAY = os.getenv("ENABLE_GATEWAY")
ZABBIX_SERVER = os.getenv("ZABBIX_SERVER")
ZABBIX_USERNAME = os.getenv("ZABBIX_USERNAME")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD")

if __name__ == '__main__':
    print(USERNAME)
    print(ZABBIX_SERVER)
    print(ZABBIX_USERNAME)