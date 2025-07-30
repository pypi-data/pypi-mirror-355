# src/proyekku/tcp_client.py

import socket
import threading
import time
import struct


class RemoteHost:
    _host = None
    _port = None
    _retry_interval = 5
    _sock = None
    _connected = False
    _lock = threading.Lock()
    _stop = False
    _on_message = None
    _reconnect_thread = None
    _receiver_thread = None

    @classmethod
    def configure(cls, host, port, retry_interval=5):
        cls._host = host
        cls._port = port
        cls._retry_interval = retry_interval

    @classmethod
    def begin_connection(cls):
        cls._stop = False

        if not cls._reconnect_thread or not cls._reconnect_thread.is_alive():
            cls._reconnect_thread = threading.Thread(target=cls._maintain_connection, daemon=True)
            cls._reconnect_thread.start()

        if not cls._receiver_thread or not cls._receiver_thread.is_alive():
            cls._receiver_thread = threading.Thread(target=cls._receiver_loop, daemon=True)
            cls._receiver_thread.start()

    @classmethod
    def _maintain_connection(cls):
        while not cls._stop:
            if not cls._connected:
                try:
                    print(f"🔌 Connecting to {cls._host}:{cls._port} ...")
                    cls._connect()
                    print("✅ Connected!")
                except Exception as e:
                    print(f"❌ Connection failed: {e}")
            time.sleep(cls._retry_interval)

    @classmethod
    def _connect(cls):
        with cls._lock:
            cls._sock = socket.create_connection((cls._host, cls._port))
            cls._connected = True

    @classmethod
    def send(cls, message: str):
        if not cls._connected:
            raise RuntimeError("Not connected to server.")
        payload = message.encode('utf-8')
        header = struct.pack('>I', len(payload))
        try:
            with cls._lock:
                cls._sock.sendall(header + payload)
        except Exception as e:
            print(f"❌ Send failed: {e}")
            cls._connected = False

    @classmethod
    def recv(cls):
        try:
            with cls._lock:
                header = cls._recv_all(4)
                if not header:
                    cls._connected = False
                    return None
                length = struct.unpack('>I', header)[0]
                data = cls._recv_all(length)
                return data.decode('utf-8') if data else None
        except Exception as e:
            print(f"❌ Receive failed: {e}")
            cls._connected = False
            return None

    @classmethod
    def _recv_all(cls, n):
        data = b''
        while len(data) < n:
            try:
                packet = cls._sock.recv(n - len(data))
            except:
                return None
            if not packet:
                return None
            data += packet
        return data

    @classmethod
    def _receiver_loop(cls):
        while not cls._stop:
            if cls._connected:
                msg = cls.recv()
                if msg and cls._on_message:
                    try:
                        cls._on_message(msg)
                    except Exception as e:
                        print(f"⚠️ Callback error: {e}")
            else:
                time.sleep(1)

    @classmethod
    def receiver_handler(cls, callback):
        cls._on_message = callback

    @classmethod
    def close(cls):
        cls._stop = True
        with cls._lock:
            if cls._sock:
                try:
                    cls._sock.close()
                except:
                    pass
                cls._sock = None
            cls._connected = False
