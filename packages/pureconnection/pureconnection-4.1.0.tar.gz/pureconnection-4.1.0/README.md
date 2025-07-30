# WELCOME TO EARTH

`pureconnection` is a OPENSOURCE lightweight realtime database based on client-server!

## Installation

You can install `pureconnection` using `pip`:


```bash
pip install pureconnection
```
Please see official PyPi website to get newer version and feature. ([Click Here](https://pypi.org/project/pureconnection))
## Example
### 1. MemoryStore 
Use this for manage data realtime on your memory
```python
from pureconnection._database import MemoryStore

# Get instance
store = MemoryStore.get_instance()

# Set key-value
store.set('ticket_no', 'SPMC')

print(store.get('ticket_no'))  # return 'SPMMC'
```
### 2. RemoteHost 
If you need data exchange with TCP protocol, you can use this method.
```python
from pureconnection._connection import RemoteHost

def on_msg(msg):
    print("📩 Server:", msg)

RemoteHost.configure("127.0.0.1", 9999)
RemoteHost.receiver_handler(on_msg)
RemoteHost.begin_connection()

# Loop utama
import time
while True:
    RemoteHost.send("PING")
    time.sleep(5)

    # Server Response
    # Server : PONG
```