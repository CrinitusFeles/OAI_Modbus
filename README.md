# OAI_Modbus

## Installation
```sh
pip install https://github.com/CrinitusFeles/OaiModbus/releases/download/v.1.1/OAI_ModBus-0.1.1-py3-none-any.whl
```
or
```sh
pip install https://github.com/CrinitusFeles/OaiModbus/releases/download/v.1.1/OAI_ModBus-0.1.1.tar.gz
```
## Update 
```sh
pip uninstall oai_modbus
```
and do [Installation](#Installation)

---

## Documentation
### OAI_Modbus.connect()
> Set connection with device
>
>Args:
>  ``` serial_num```- *[str]*: string of device's serial number.
>
>Returns:
>  ``` 0``` - success connection.
> ``` -1``` - connection issues.

### OAI_Modbus.disconnect()
>  
>Args:
>  ```None```
>
>Returns:
>  ``` 0``` - success disconnected.
> ``` -1``` - device was not connected.

### OAI_Modbus.get_connected_devices()
> Returns all connected devices.
>
>Args:
>  ``` None```
>
>Returns:
>  *[list]*: list consisting ['uart com port', 'serial number']

### OAI_Modbus.read_regs(target='ai')
>Reading list ranges of analog input or output register. List ranges need to set in advance.
>
>Args:
>  ``` target```- *[str]:* available parameters is *'ai'* - analog inputs or *'ao'* - analog outputs  
>
>Returns:
>  *[list]*: register map of analog inputs or analog autputs 

### OAI_Modbus.write_regs()
>Writing lists of registers. List ranges need to set in advance.
>
>Args:
>  ``` None```
>
>Returns:
>  ``` None```

### OAI_Modbus.start_continuously_queue_reading()
>Starts read *'ao'* and *'ai'* regs in different thread. Before using you should to assign ``` self.queues_survey_flag``` and ``` self.continuously_ai(ao)_flag ```
>
>Args:
>  ``` None```
>
>Returns:
>  ``` None```

## Usage
```py 
from oai_modbus import OAI_Modbus


if __name__ == '__main__':
    client = OAI_Modbus(serial_num=['20733699424D'], debug=True)  # serial_num - rewrites list of serial numbers devices 
                                                                # debug - flag for print debug information
    print(client.get_connected_devices())  # print data about all connected devices
    client.connect()  # try to connect to someone
    if client.connection_status:  
        client.continuously_ao_flag = True  # indicate which registers we will read in thread (ai/ao) 
        client.continuously_ai_flag = True
        client.single_ao_flag = False   # if you need to read registers just one time you should use this flags
        client.single_ai_flag = False

        client.ao_read_ranges = [[0, 3], [12, 13], [216, 925]]  # [start address (included); stop address (not included)]
        client.ai_read_ranges = [[0, 3], [5, 12]] 
        
        # [start address, [data to write]], [next start address, [data to write]]
        client.write_ranges = [[0, [3, 5, 7, 2]], [8, [12, 2, 5, 7, 0, 1, 5, 7, 889, 33, 332, 2, 4, 5]]]  
        
        print("before write:", client.read_regs(target='ao')[0:100])  # you can write only in analog outputs registers
        client.write_regs()
        print("after write:", client.read_regs(target='ao')[0:100])   
        
        client.start_continuously_queue_reading()  # start read in thread 
        
        test_value = 0
        while True:
            client.write_ranges = [[0, [test_value, test_value+1, test_value+2]], [8, [test_value+3, test_value+4]]]
            time.sleep(1)
            print("ai register_map:", client.ai_register_map[:10])
            print("ao register_map:", client.ao_register_map[:10])
            test_value += 1
    
```

## Dependencies
Depends on these packages:
1. [pymodbus](https://pymodbus.readthedocs.io/en/latest/)
