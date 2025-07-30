from pureconnection._database import MemoryStore
import time

store = MemoryStore.get_instance()

store.set('ticket_no', 'SPMC')

while True:
    print(store.get('ticket_no'))
    time.sleep(5)