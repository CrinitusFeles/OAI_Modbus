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
### OAI_Modbus.connect(serial_num='')
> Set connection with device. *serial_num* appends serial number to list of all serial numbers 
>
>Args:
>  ``` serial_num```- *[str]*: string of device's serial number.
>
>Returns:
>  ``` 1``` - success connection.
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

### OAI_Modbus.read_regs(target='ai', read_ranges=None)
>Reading list ranges of analog input or output register. List ranges need to set in advance.
>
>Args:
>  ``` target```- *[str]:* available parameters is *'ai'* - analog inputs or *'ao'* - analog outputs.
>  ``` read_ranges```- *[list]:* list of ranges that will be read .
>
>Returns:
>  *[list]*: register map of analog inputs or analog autputs 

### OAI_Modbus.write_regs(offset, data_list)
>Writing lists of registers. List ranges need to set in advance.
>
>Args:
>  ``` offset```- *[int]:* address where will be written the first byte from ```data_list```.
>  ``` data_list```- *[list]:* 
>
>Returns:
>  ``` None```

### OAI_Modbus.start_continuously_queue_reading(ai=None, ao=None, write=None)
>Starts read *'ao'* and *'ai'* regs in different thread. If parameter is empty list the thread will not be read it. 
>
>Args:
>  ``` ai```- *[list]:* list of addresses ranges of analog inputs.
>  ``` ao```- *[list]:* list of addresses ranges of analog outputs.
>  ``` write```- *[list]:* write ranges in format [offset, [data_list]].
>
>Returns:
>  ``` None```

---

## Usage
```py 
try:
    from oai_modbus import OAI_Modbus
except ImportError:
    print("use github installer")
import time

if __name__ == '__main__':
    client = OAI_Modbus(serial_num=['20733699424D', '20703699424D'], debug=True)
    print(client.get_connected_devices())
    client.connect()
    test_mode = False  # for debug

    if client.connection_status:
        if test_mode:
            # ---- test write -----
            print("before write:", client.read_regs(target='ao', read_ranges=[[0, 3]]))
            client.write_regs(offset=0, data_list=[1, 2, 3, 4, 5])
            print("after write:", client.read_regs(target='ao', read_ranges=[[0, 3]]))
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
    
```

---

## Dependencies
Depends on these packages:
1. [pymodbus](https://pymodbus.readthedocs.io/en/latest/)
