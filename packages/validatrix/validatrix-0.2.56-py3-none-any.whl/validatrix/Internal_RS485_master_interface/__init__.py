"""
RS485 master Interface module for Validatrix.
Provides functionality for RS485 data monitoring as master Device
"""

from .Internal_RS485_master import *
from .Internal_RS485_master_server import *
from .Internal_RS485_device_data import *

__all__ = [
    'Internal_RS485_master_class',
    'Internal_RS485_master_server_class',
] 