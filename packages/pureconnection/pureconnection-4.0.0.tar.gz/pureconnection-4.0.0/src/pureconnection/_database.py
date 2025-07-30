# src/pureconnection/_database.py

import time, threading

class MemoryStore:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._store = {}
        self._ttl = {}
        self._data_lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set(self, key, value, expire=None):
        with self._data_lock:
            self._store[key] = value
            if expire:
                self._ttl[key] = time.time() + expire

    def get(self, key):
        with self._data_lock:
            if self._is_expired(key):
                self._delete_internal(key)
                return None
            return self._store.get(key)

    def delete(self, key):
        with self._data_lock:
            self._delete_internal(key)

    def exists(self, key):
        with self._data_lock:
            if self._is_expired(key):
                self._delete_internal(key)
                return False
            return key in self._store

    def keys(self):
        with self._data_lock:
            return [k for k in self._store.keys() if not self._is_expired(k)]

    def _delete_internal(self, key):
        self._store.pop(key, None)
        self._ttl.pop(key, None)

    def _is_expired(self, key):
        exp = self._ttl.get(key)
        return exp is not None and time.time() > exp
