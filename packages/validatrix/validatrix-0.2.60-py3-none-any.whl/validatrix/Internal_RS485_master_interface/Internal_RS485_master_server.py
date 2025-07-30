
from time import sleep
from threading import Thread, Event
import asyncio
import serial

from pymodbus.client import ModbusSerialClient as msc
from pymodbus.payload import BinaryPayloadDecoder as pp
from pymodbus.transaction import ModbusRtuFramer

#####make sure that pymodbus version in sudo pip3 is 3.1.3

class Internal_RS485_master_server_class:
    def __init__(self,hw_channal=None,baudrate=None,parity='None',stopbits=1,timeout=1):        
        self.hw_channal=hw_channal
        self.baudrate=baudrate
        self.master_dict={}        
        self.server=None
        self.timeout=timeout
        self.server_thread=None
        self.stop_server_flag=1
        self.parity=parity
        self.stopbits=stopbits
    
    def add_master(self,master_id):
        self.master_dict[master_id] = master_id
       
        ###all slaves are active by default

    ### function to update slaves context, to be run every time coltext is updated
    def connect_server_function(self):
        p=""
        if self.parity == 'None':
            p="N"
        elif self.parity == 'Even':
            p="E"
        elif self.parity == 'Odd':
            p="O"
        try:
            # Create a Modbus server context with the active slaves            
            self.server= msc(method='rtu',port=self.hw_channal,baudrate=self.baudrate,bytesize=8,
                            parity=p,stopbits=self.stopbits,timeout=self.timeout)
            connection= self.server.connect()
            print("Connected to RS485 master server: "+str(connection))
        except Exception as e:
            print("Error in connecting to server: "+str(e))
            connection=False

    def read_hold_register_data(self,address,start_reg,reg_count):
        """Read holding registers from the Modbus server."""
        try:
            print(f"Reading {reg_count} registers starting from {start_reg} at address {address}")
            try:
                response = self.server.read_holding_registers(address=start_reg, count=reg_count, slave=address)
            except Exception as e:
                print(f"Exception while reading registers: {e}")
            
            # print(response)
            if response.isError():
                print(f"Error reading registers: {response}")
                return []
            return response.registers
        except Exception as e:
            print(f"Exception while reading registers: {e}")
            return None 
    
    def stop_server(self):
        """Stop the Modbus server."""
        if self.server is not None:
            try:
                self.server.close()
                print("RS485 Modbus master server stopped.")
            except Exception as e:
                print(f"Error stopping Modbus server: {e}")
            finally:
                self.server = None
        else:
            print("No Modbus server to stop.")
