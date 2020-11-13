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

        self.ao_register_map = [0] * 10**4
        self.ai_register_map = [0] * 10**4
        self.__last_read_ao_range = []
        self.__last_read_ai_range = []
        self.ao_read_ranges = [[0, 3], [12, 13], [216, 925]]
        self.ai_read_ranges = [[0, 3], [5, 12]]  # [start address (included); stop address (not included)]
        self.write_ranges = [[0, [3, 5, 7, 2]], [8, [12, 2, 5, 7, 0, 1, 5, 7, 889, 33, 332, 2, 4, 5]]]
        self.reverse_bytes_flag = True

        # thread flags
        self.continuously_ao_flag = False
        self.continuously_ai_flag = False
        self.single_ao_flag = False
        self.single_ai_flag = False
        self.queues_survey_flag = False
        self.continuously_write_flag = False

        self.read_thread = threading.Thread(name='queue', target=self.__queue_continuously_survey, daemon=True)

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

    def read_regs(self, target="ai"):
        """
        Reading list of analog input or output register.
        :param target: ai - analog inputs; ao - analog outputs.
        :return: register's map of analog inputs or outputs.
        """
        if target == 'ai':
            last_read_range = self.__last_read_ai_range
            read_ranges = self.ai_read_ranges
            register_map = self.ai_register_map
            target_function = self.modbus_client.read_input_registers
            print_string = "ai"
        else:
            last_read_range = self.__last_read_ao_range
            read_ranges = self.ao_read_ranges
            register_map = self.ao_register_map
            target_function = self.modbus_client.read_holding_registers
            print_string = "ao"
        # else:
        #     print("TARGET ERROR")

        for k in range(len(read_ranges)):
            last_read_range.clear()
            count = read_ranges[k][1] - read_ranges[k][0]
            if read_ranges[k][0] >= read_ranges[k][1]:
                print(print_string, "range", k, "error")
                raise ValueError("RANGE ERROR")
            for i in (lambda x: range((x//10) + 1) if (x//10 >= 1 or x < 10) and x % 10 != 0 else range(x//10))(count):
                try:
                    register_list = target_function(
                        read_ranges[k][0] + i * 10,
                        (lambda x: x if x < 10 else 10)(count),
                        unit=1
                    )
                    count -= 10
                    if self.reverse_bytes_flag:
                        buf_reg = []
                        for j in register_list.registers:
                            if j > 255:
                                buf_reg.append((j >> 8) | ((j & 0xFF) << 8))
                            else:
                                buf_reg.append(j << 8)
                        last_read_range.extend(buf_reg)
                    else:
                        last_read_range.extend(register_list.registers)
                except Exception as error:
                    print(error)

            for i in range(read_ranges[k][1] - read_ranges[k][0]):
                register_map[read_ranges[k][0] + i] = last_read_range[i]
            # print(print_string, " range[", k, "]: ", last_read_range)
        return register_map

    def write_regs(self):
        """
        Writing lists of registers.
        :return: None.
        """
        if self.reverse_bytes_flag:
            buf_reg = []
            buf = []
            for j in self.write_ranges:
                for k in j[1]:
                    buf.append((k >> 8) | ((k & 0xFF) << 8))
                buf_reg.append([j[0], buf])
                buf = []
            self.write_ranges = buf_reg
            print("buf_reg: ", buf_reg)

        for k in range(len(self.write_ranges)):
            for i in range(0, len(self.write_ranges[k][1]), 10):
                try:
                    self.modbus_client.write_registers(self.write_ranges[k][0] + i, self.write_ranges[k][1][i: i + 10],
                                                       unit=1)
                except Exception as error:
                    print(error)

    def stop_continuously_ai_reading(self):
        self.continuously_ai_flag = False

    def stop_continuously_ao_reading(self):
        self.continuously_ao_flag = False

    def start_continuously_queue_reading(self):
        """
        Start read ao and ai regs in different thread. Before using you should to assign self.queues_survey_flag and
        self.continuously_ai(ao)_flag
        :return: None
        """
        self.queues_survey_flag = True
        self.read_thread.start()

        if not self.read_thread.is_alive():
            self.queues_survey_flag = False
            print("some error with thread")

    def __queue_continuously_survey(self):
        while self.queues_survey_flag:
            if self.single_ao_flag:
                try:
                    self.read_regs(target='ao')
                except ValueError as error:
                    print(error)
                self.single_ao_flag = False
            if self.single_ai_flag:
                self.read_regs(target='ai')
                self.single_ai_flag = False

            if self.continuously_ao_flag:
                try:
                    self.read_regs(target='ao')
                except ValueError as error:
                    print(error)
            if self.continuously_ai_flag:
                self.read_regs(target='ai')
            if self.continuously_write_flag:
                self.write_regs()
                self.continuously_write_flag = False


if __name__ == '__main__':
    # Attention!!! Before first launch add serial number of your device in "self.serial_numbers" (string 12)
    client = OaiModbus()
    client.connect()
    client.continuously_ao_flag = True
    client.continuously_ai_flag = True
    client.single_ao_flag = False
    client.single_ai_flag = False
    test_mode = True  # for debug

    if client.connection_status:
        if test_mode:
            # ---- test write -----
            print("before write:", client.read_regs(target='ao'))
            client.write_regs()
            print("after write:", client.read_regs(target='ao'))
            # ---------------------
        else:
            client.start_continuously_queue_reading()
            time.sleep(5)
            client.write_regs()
            time.sleep(5)
            client.queues_survey_flag = False
        print("ai register_map:", client.ai_register_map[:1000])
        print("ao register_map:", client.ao_register_map[:1000])

    else:
        print("connection issues")
