from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import serial.tools.list_ports
import threading
import time
#v1.1.1 BREAKING CHANGE!!

class OAI_Modbus(ModbusClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.serial_numbers = kwargs.get('serial_num', ['2057359A5748'])
        self.baudrate = kwargs.get('baudrate', 115200)
        self.timeout = 1
        self.port = ''
        self.connection_status = False
        self.no_answer_counter = 0

        self.modbus_client = None
        self.debug_print_flag = kwargs.get('debug', True)
        self.lock = threading.Lock()

        self.ao_register_map = [0] * 10**4
        self.ai_register_map = [0] * 10**4
        self.__last_read_ao_range = []
        self.__last_read_ai_range = []
        self.ao_read_ranges = [[]]
        self.ai_read_ranges = [[]]  # [start address (included); stop address (not included)]
        self.write_ranges = [[[]]]
        self.reverse_bytes_flag = kwargs.get('reverse_bytes', True)
        self.time_sleep = kwargs.get('time_sleep', 0.03)

        # thread flags
        self.continuously_ao_flag = False
        self.continuously_ai_flag = False
        self.single_ao_flag = False
        self.single_ai_flag = False
        self.queues_survey_flag = False
        self.continuously_write_flag = False

        self.read_thread = None

    def debug_print(self, string):
        if self.debug_print_flag:
            print(string)

    def connect(self, serial_num='2057359A5748'):
        """
        Set connection with device via serial port.
        :param: serial_num - str of serial number which will be appended to list of all serial numbers
        :return: 1 - success connection
                 1 - device already connected
                -1 - failed connection
        """
        
        self.serial_numbers.append(serial_num)
        if self.connection_status:
            return 1
        else:
            try:
                if self.__get_overlap():
                    self.modbus_client = ModbusClient(method='rtu', port=self.port, baudrate=self.baudrate, parity='N',
                                                      timeout=self.timeout, write_timeout=2)
                    if self.modbus_client.connect():
                        self.connection_status = True
                        self.read_thread = threading.Thread(name='queue', target=self.queue_continuously_survey, daemon=True)
                        self.debug_print("success connection")
                        return 1
                    else:
                        self.connection_status = False
                        self.debug_print("failed connection")
                        return -1
                else:
                    self.debug_print("connected devices: ", self.get_connected_devices())
                    self.connection_status = False
                    self.debug_print("ERROR: devices not detected")
                    return -1

            except Exception as error:
                self.debug_print(error)

    def close_all_processes(self):
        self.continuously_ao_flag = False
        self.continuously_ai_flag = False
        self.single_ao_flag = False
        self.single_ai_flag = False
        self.queues_survey_flag = False
        self.continuously_write_flag = False
        self.modbus_client.close()
        self.connection_status = False
        self.read_thread = None

    def disconnect(self):
        if self.connection_status:
            self.close_all_processes()
            self.debug_print("disconnected")
            return 0
        else:
            self.debug_print("device not connected")
            return -1

    def get_connected_devices(self):
        serial_num_list = []
        try:
            com_list = serial.tools.list_ports.comports()
            if len(com_list) == 0:
                self.debug_print("There is no connected devices")
                return []
            self.debug_print('\nDetected the following serial ports:')
            for com in com_list:
                self.debug_print('Port:%s\tID#:=%s' % (com.device, com.serial_number))
                serial_num_list.append([com.device, com.serial_number])
            return serial_num_list
        except Exception as error:
            self.debug_print(error)

    def __get_overlap(self):
        """
        Internal function for definition of usb ID from list of available devices (self.serial_numbers).
        :return: connection status (True - successful connection; False - failed connection).
        if error - returns connected devices serial num list
        """
        try:
            ser_nums = self.get_connected_devices()
            for com in ser_nums:
                if com[1] != '':
                    for ID in self.serial_numbers:
                        self.debug_print(["ID: ", ID, "com: ", com[1]])
                        if com[1].__str__()[:len(ID)] == ID:  # Match ID with the correct port
                            self.port = com[0]  # Store the device name to later open port with.
                            return True
            return False
        except Exception as error:
            self.debug_print("OAI_Modbus.py __get_overlap error: ", error)

    def read_regs(self, target="ai", read_ranges=None):
        """
        Reading list of analog input or output register.
        :param target: ai - analog inputs; ao - analog outputs.
        :param read_ranges: list of lists register ranges
        :return: register's map of analog inputs or outputs.
        """
        if target == 'ai':
            last_read_range = self.__last_read_ai_range
            read_ranges = read_ranges
            register_map = self.ai_register_map
            target_function = self.modbus_client.read_input_registers
            print_string = "ai"
        else:
            last_read_range = self.__last_read_ao_range
            read_ranges = read_ranges
            register_map = self.ao_register_map
            target_function = self.modbus_client.read_holding_registers
            print_string = "ao"
        # else:
        #     print("TARGET ERROR")
        error_flag = False
        with self.lock:
            for k in range(len(read_ranges)):
                last_read_range.clear()
                count = read_ranges[k][1] - read_ranges[k][0]
                if read_ranges[k][0] >= read_ranges[k][1]:
                    self.debug_print([print_string, "range", k, "error"])
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
                        self.debug_print("error in modbus module: function read_regs")
                        self.debug_print(error)
                        self.close_all_processes()
                        if self.read_thread is not None:
                            if self.read_thread.is_alive():
                                print('thread is alive')
                        else:
                            print('oai_modbus thread is None')
                        error_flag = True
                        break

                    if error_flag:
                        break
                try:
                    for i in range(read_ranges[k][1] - read_ranges[k][0]):
                        register_map[read_ranges[k][0] + i] = last_read_range[i]
                except Exception as error:
                    self.no_answer_counter += 1
                    self.debug_print("Modbus read timeout error")
                # print(print_string, " range[", k, "]: ", last_read_range)

        slice_register_map = [register_map[r[0]:r[-1]] for r in read_ranges]
        return slice_register_map

    def write_regs(self, offset, data_list):
        """
        Writing lists of registers.
        :param: offset: register's address from which will write data_list
        :param: data_list:
        :return: None.
        """
        if self.connection_status:
            self.write_ranges = [[offset, data_list]]
            self.write_regs_ranges()
        else:
            print('error in write_regs: no connection with device. Try to reconnect')

    def write_regs_ranges(self):
        """
        Writing lists of registers.
        :return: None.
        """
        with self.lock:
            if self.reverse_bytes_flag:
                buf_reg = []
                buf = []
                for j in self.write_ranges:
                    for k in j[1]:
                        buf.append((k >> 8) | ((k & 0xFF) << 8))
                    buf_reg.append([j[0], buf])
                    buf = []
                self.write_ranges = buf_reg

            error_flag = False
            for k in range(len(self.write_ranges)):
                for i in range(0, len(self.write_ranges[k][1]), 10):
                    try:
                        answer = self.modbus_client.write_registers(self.write_ranges[k][0] + i,
                                                           self.write_ranges[k][1][i: i + 10], unit=1)

                        if answer.address != self.write_ranges[k][0]:
                            self.no_answer_counter += 1
                            self.debug_print("Modbus write timeout error")
                    except Exception as error:
                        self.no_answer_counter += 1
                        self.debug_print('Modbus module has issue in function write_regs_ranges')
                        self.debug_print(error)
                        self.close_all_processes()
                        error_flag = True
                        break
                if error_flag:
                    break

    def stop_continuously_ai_reading(self):
        self.continuously_ai_flag = False

    def stop_continuously_ao_reading(self):
        self.continuously_ao_flag = False

    def start_continuously_queue_reading(self, ai=None, ao=None, write=None):
        """
        Start read ao and ai regs in different thread. Before using you should to assign self.queues_survey_flag and
        self.continuously_ai(ao)_flag
        :return: None
        """
        if len(ai) > 0:
            self.continuously_ai_flag = True
            self.ai_read_ranges = ai
        if len(ao) > 0:
            self.continuously_ao_flag = True
            self.ao_read_ranges = ao
        if len(write) > 0:
            print(len(write))
            self.continuously_write_flag = True
            self.write_ranges = write

        if self.read_thread is not None:
            if self.read_thread.is_alive():
                pass
            else:
                self.queues_survey_flag = True
                self.read_thread.start()
        else:
            self.read_thread = threading.Thread(name='queue', target=self.queue_continuously_survey, daemon=True)
        if not self.read_thread.is_alive():
            self.queues_survey_flag = True
            self.read_thread.start()

    def queue_continuously_survey(self):
        while self.queues_survey_flag and self.connection_status:
            # print('thread in _queue_continuously_survey')
            if self.single_ao_flag:
                try:
                    self.read_regs(target='ao', read_ranges=self.ao_read_ranges)
                except ValueError as error:
                    self.debug_print('error "single read ao regs" in function queue_continuously_survey')
                    self.debug_print(error)
                self.single_ao_flag = False
            if self.single_ai_flag:
                self.read_regs(target='ai', read_ranges=self.ai_read_ranges)
                self.single_ai_flag = False

            if self.continuously_ao_flag:
                try:
                    self.read_regs(target='ao', read_ranges=self.ao_read_ranges)
                except ValueError as error:
                    self.debug_print('error "continuously read ao regs" in function queue_continuously_survey')
                    self.debug_print(error)
            if self.continuously_ai_flag:
                self.read_regs(target='ai', read_ranges=self.ai_read_ranges)
            if self.continuously_write_flag:
                self.write_regs(self.write_ranges[0], self.write_ranges[1])
                self.continuously_write_flag = False
            time.sleep(self.time_sleep)
        if not self.connection_status:
            self.debug_print('Modbus module has lost connection with device')

if __name__ == '__main__':
    client = OAI_Modbus(serial_num=['20703699424D', '20703699424D'], debug=True)
    print(client.get_connected_devices())
    client.connect()
    test_mode = False  # for debug

    if client.connection_status:
        print('connection status: ' + str(client.connection_status))
        if test_mode:
            # ---- test write -----
            print("before write:", client.read_regs(target='ao', read_ranges=[[0, 5]])[0:5])
            client.write_regs(offset=0, data_list=[1, 2, 3, 4, 5])
            print("after write:", client.read_regs(target='ao', read_ranges=[[0, 5]])[0:5])
            # ---------------------
        else:
            client.start_continuously_queue_reading(ai=[[0, 3], [12, 14]], ao=[[0, 8], [12, 15]], write=[])
            time.sleep(1)
            val = 0
            while True:
                client.write_regs(offset=0, data_list=[val, val+1, val+2, val+3])
                time.sleep(1)
                # client.queues_survey_flag = False
                print("ai register_map:", client.ai_register_map[:5])
                print("ao register_map:", client.ao_register_map[:5])
                val += 1

    else:
        print("connection issues")
