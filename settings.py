import os
from dotenv import load_dotenv

load_dotenv()

RO_COMMUNITY = os.getenv('RO_COMMUNITY')
RW_COMMUNITY = os.getenv("RW_COMMUNITY")
USERNAME = os.getenv("USERNAME")
PASSWORDS = os.getenv("PASSWORDS").split(',')
ENABLE = os.getenv("ENABLE")
USERNAME_GATEWAY= os.getenv("USERNAME_GATEWAY")
PASSWORD_GATEWAY= os.getenv("PASSWORD_GATEWAY")
ENABLE_GATEWAY = os.getenv("ENABLE_GATEWAY")