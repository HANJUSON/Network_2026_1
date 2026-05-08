socket = __import__('socket')


class HFTClientBase:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None
            self.connected = False

    def send_order(self, order) -> int:
        raise NotImplementedError

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class HFTClientTCP(HFTClientBase):
    def __init__(self, host: str, port: int, nodelay: bool = True, timeout_ms: int = 1000):
        super().__init__(host, port)
        self.nodelay = nodelay
        self.timeout_sec = timeout_ms / 1000.0

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout_sec)
        
        if self.nodelay:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        self.sock.connect((self.host, self.port))
        self.connected = True

    def send_order(self, order) -> int:
        from src.utils import get_time_ns
        start_ns = get_time_ns()
        
        self.sock.sendall(order.serialize())
        response_data = self.sock.recv(1024)
        
        end_ns = get_time_ns()
        return end_ns - start_ns


class HFTClientUDP(HFTClientBase):
    def __init__(self, host: str, port: int, timeout_ms: int = 1000):
        super().__init__(host, port)
        self.timeout_sec = timeout_ms / 1000.0

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout_sec)
        self.sock.connect((self.host, self.port))
        self.connected = True

    def send_order(self, order) -> int:
        from src.utils import get_time_ns
        start_ns = get_time_ns()

        self.sock.send(order.serialize())

        try:
            response_data = self.sock.recv(1024)
        except socket.timeout:
            return -1

        end_ns = get_time_ns()
        return end_ns - start_ns


def create_client(host: str, port: int, protocol: str = 'tcp', **kwargs):
    if protocol.lower() == 'tcp':
        return HFTClientTCP(host, port, **kwargs)
    elif protocol.lower() == 'udp':
        timeout_ms = kwargs.get('timeout_ms', 1000)
        return HFTClientUDP(host, port, timeout_ms=timeout_ms)
    else:
        raise ValueError(f"Unknown protocol: {protocol}")
