import socket
import threading
import struct
import time

class RemoteHost:
    _host = None
    _port = None
    _sock = None
    _connected = False
    _on_message = None
    _receiver_thread = None
    _reconnect_thread = None
    _stop = False

    @classmethod
    def configure(cls, host, port):
        cls._host = host
        cls._port = port

    @classmethod
    def receiver_handler(cls, callback):
        cls._on_message = callback

    @classmethod
    def begin_connection(cls):
        cls._stop = False
        cls._reconnect_thread = threading.Thread(target=cls._reconnect_loop, daemon=True)
        cls._reconnect_thread.start()

    @classmethod
    def _connect(cls):
        try:
            cls._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cls._sock.settimeout(5)
            cls._sock.connect((cls._host, cls._port))
            cls._sock.settimeout(None)
            cls._connected = True
            print(f"✅ Connected to {cls._host}:{cls._port}")
            cls._receiver_thread = threading.Thread(target=cls._receiver_loop, daemon=True)
            cls._receiver_thread.start()
        except Exception as e:
            cls._connected = False
            print(f"❌ Connect failed: {e}")

    @classmethod
    def _reconnect_loop(cls):
        while not cls._stop:
            if not cls._connected:
                print(f"🔁 Trying to connect to {cls._host}:{cls._port}")
                cls._connect()
            time.sleep(2)

    @classmethod
    def _receiver_loop(cls):
        print("📡 Receiver started")
        while cls._connected and not cls._stop:
            try:
                header = cls._recv_all(4)
                if not header:
                    raise ConnectionResetError("Lost header")
                length = struct.unpack('>I', header)[0]
                data = cls._recv_all(length)
                if not data:
                    raise ConnectionResetError("Lost payload")
                message = data.decode('utf-8')
                print(f"📩 Received: {message}")
                if cls._on_message:
                    cls._on_message(message)
            except Exception as e:
                print(f"⚠️ Receiver error: {e}")
                cls._connected = False
                if cls._sock:
                    cls._sock.close()
                    cls._sock = None
                break

    @classmethod
    def _recv_all(cls, n):
        data = b''
        while len(data) < n:
            part = cls._sock.recv(n - len(data))
            if not part:
                return None
            data += part
        return data

    @classmethod
    def send(cls, message: str):
        if not cls._connected or not cls._sock:
            print("⚠️ Not connected, cannot send.")
            return
        payload = message.encode('utf-8')
        header = struct.pack('>I', len(payload))
        try:
            cls._sock.sendall(header + payload)
        except Exception as e:
            print(f"❌ Send failed: {e}")
            cls._connected = False
            if cls._sock:
                cls._sock.close()
                cls._sock = None

    @classmethod
    def is_connected(cls):
        return cls._connected

    @classmethod
    def wait_until_connected(cls, timeout=10):
        start = time.time()
        while not cls._connected:
            if time.time() - start > timeout:
                raise TimeoutError("Timeout waiting for connection.")
            time.sleep(0.1)

    @classmethod
    def stop(cls):
        cls._stop = True
        if cls._sock:
            cls._sock.close()
        cls._connected = False