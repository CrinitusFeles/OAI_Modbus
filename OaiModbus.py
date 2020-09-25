from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import serial.tools.list_ports
import threading
import time


class OaiModbus(ModbusClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.serial_numbers = ['2057359A5748']  # you need to add the new ID of your devices YOURSELF.
        self.baudrate = 115200
        self.timeout = 1
        self.port = ''
        self.connection_status = False
        self.modbus_client = None

        self.actual_ao_regs = []
        self.actual_ai_regs = []
        self.continuously_ao_flag = False
        self.continuously_ai_flag = False

    def connect(self):
        """
        Set connection with device via serial port.
        :return: None
        """
        try:
            if self.__get_id():
                self.modbus_client = ModbusClient(method='rtu', port=self.port, baudrate=self.baudrate, parity='N',
                                                  timeout=self.timeout)
                if self.modbus_client.connect():
                    print("success connection")
                else:
                    print("failed connection")
            else:
                print("ERROR: devices not detected")

        except Exception as error:
            print(error)

    def __get_id(self):
        """
        Internal function for definition of usb ID from list of available devices (self.serial_numbers).
        :return: connection status (True - successful connection; False - failed connection.
        """
        try:
            com_list = serial.tools.list_ports.comports()
            if len(com_list) == 0:
                print("There is no connected devices")
                self.connection_status = False
                return self.connection_status
            # print('\nDetected the following serial ports:')
            for com in com_list:
                # print('Port:%s\tID#:=%s' % (com.device, com.serial_number))
                for ID in self.serial_numbers:
                    if com.serial_number is not None:
                        if com.serial_number.__str__()[:len(ID)] == ID:  # Match ID with the correct port
                            self.port = com.device  # Store the device name to later open port with.
                            self.connection_status = True
                            return self.connection_status
        except Exception as error:
            print(error)

    def read_ao_regs(self, address=0, count=1):
        """
        Reading list of analog output register.
        :param address: start address (min = 0; max = 10000).
        :param count: amount of reading registers (min = 1; max = 120).
        :return: list of 2-byte registers.
        """
        try:
            register_list = self.modbus_client.read_holding_registers(address, count, unit=1)
            self.actual_ao_regs.clear()
            self.actual_ao_regs = register_list.registers
            return self.actual_ao_regs
        except Exception as error:
            print(error)

    def read_ai_regs(self, address=0, count=1):
        """
        Reading list of analog input register.
        :param address: start address (min = 0; max = 10000).
        :param count: amount of reading registers (min = 1; max = 120).
        :return: list of 2-byte registers.
        """
        try:
            register_list = self.modbus_client.read_input_registers(address, count, unit=1)
            self.actual_ai_regs.clear()
            self.actual_ai_regs = register_list.registers
            return self.actual_ai_regs
        except Exception as error:
            print(error)

    def write_regs(self, address, values):
        """
        Writing list of registers.
        :param address: address of first register where will be write list.
        :param values: list of values which will be writen to address.
        :return: None.
        """

        try:
            self.modbus_client.write_registers(address, values, unit=1)
        except Exception as error:
            print(error)

    def start_continuously_ao_reading(self, address=0, count=1, delay=1):
        """
        Start periodic request "analog output" regs.
        :param address: start address (min = 0; max = 10000).
        :param count:  amount of reading registers (min = 1; max = 120).
        :param delay: delay in seconds between requests.
        :return: None

        NOTE: for gui app the thread should be daemon
        """
        self.continuously_ao_flag = True
        t = threading.Thread(name='ao_read', target=self.__get_actual_ao_regs,
                             daemon=False, kwargs={'address': address, 'count': count, 'delay': delay})
        t.start()

        if not t.is_alive():
            self.continuously_ao_flag = False
            print("some error with thread")

    def start_continuously_ai_reading(self, address=0, count=1, delay=1):
        """
        Start periodic request "analog input" regs.
        :param address: start address (min = 0; max = 10000).
        :param count:  amount of reading registers (min = 1; max = 120).
        :param delay: delay in seconds between requests.
        :return: None

        NOTE: for gui app the thread should be daemon
        """
        self.continuously_ai_flag = True
        t = threading.Thread(name='ai_read', target=self.__get_actual_ai_regs,
                             daemon=False, kwargs={'address': address, 'count': count, 'delay': delay})
        t.start()

        if not t.is_alive():
            self.continuously_ai_flag = False
            print("some error with thread")

    def stop_continuously_ai_reading(self):
        self.continuously_ai_flag = False

    def stop_continuously_ao_reading(self):
        self.continuously_ao_flag = False

    def __get_actual_ao_regs(self, address=0, count=1, delay=1):
        while self.continuously_ao_flag:
            print(self.read_ao_regs(address=address, count=count))
            time.sleep(delay)

    def __get_actual_ai_regs(self, address=0, count=1, delay=1):
        while self.continuously_ai_flag:
            print(self.read_ai_regs(address=address, count=count))
            time.sleep(delay)

    # def connection_check(self):
    #     if not self.connection_status:
    #         print("device does not connect")


if __name__ == '__main__':
    client = OaiModbus()
    client.connect()
    if client.connection_status:
        client.write_regs(0, [1, 2, 5, 10])
        print(client.read_ao_regs(0, 10))
        # print(client.read_ai_regs(0, 10))
        client.start_continuously_ai_reading(address=0, count=10, delay=1)
        client.start_continuously_ao_reading(address=0, count=20, delay=1)
    else:
        print("connection issues")
