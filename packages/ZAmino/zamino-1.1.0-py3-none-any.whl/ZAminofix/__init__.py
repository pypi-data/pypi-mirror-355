__title__ = 'Sorex'
__author__ = 'Sor'
__version__ = '0.5.0'

from .acm import ACM
from .client import Client
from .sub_client import SubClient
from .lib.util import exceptions, helpers, objects, headers
from .socket import Callbacks, SocketHandler
from requests import get
from json import loads
from os import system, name
from colorama import Fore

# Clean the screen
if name == "nt": 
    system("cls")  # Windows
else: 
    system("clear")  # Unix/Linux

# Display attribution
print(Fore.LIGHTCYAN_EX + f"[✦] Sorex - Made By Sor" + Fore.RESET)