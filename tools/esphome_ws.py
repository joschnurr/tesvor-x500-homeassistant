#!/usr/bin/env python3
"""Minimaler WebSocket-Client für den ESPHome-Device-Builder (ws://host:6052/ws), ohne Zusatzmodule."""
import socket, struct, os, base64, json, sys, time

HOST = os.getenv("ESPHOME_HOST", "127.0.0.1")   # Host des ESPHome-Dashboards
PORT = int(os.getenv("ESPHOME_PORT", "6052"))

class WS:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET /ws HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: http://{HOST}:{PORT}\r\n\r\n")
        self.s.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        head, _, rest = buf.partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise SystemExit("Handshake fehlgeschlagen: " + head.decode(errors="replace")[:200])
        self.buf = rest
        self.mid = 0

    def _read(self, n):
        while len(self.buf) < n:
            d = self.s.recv(65536)
            if not d:
                raise ConnectionError("Verbindung geschlossen")
            self.buf += d
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def recv(self):
        while True:
            b0, b1 = self._read(2)
            op = b0 & 0x0F
            ln = b1 & 0x7F
            if ln == 126: ln = struct.unpack(">H", self._read(2))[0]
            elif ln == 127: ln = struct.unpack(">Q", self._read(8))[0]
            mask = self._read(4) if b1 & 0x80 else None
            data = self._read(ln)
            if mask: data = bytes(c ^ mask[i % 4] for i, c in enumerate(data))
            if op == 0x1: return json.loads(data.decode())
            if op == 0x9: self._send(0xA, data)       # Ping -> Pong
            if op == 0x8: raise ConnectionError("Server schließt")

    def _send(self, op, data):
        mask = os.urandom(4)
        hdr = bytes([0x80 | op])
        n = len(data)
        if n < 126: hdr += bytes([0x80 | n])
        elif n < 65536: hdr += bytes([0x80 | 126]) + struct.pack(">H", n)
        else: hdr += bytes([0x80 | 127]) + struct.pack(">Q", n)
        self.s.sendall(hdr + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(data)))

    def send(self, command, **args):
        self.mid += 1
        self._send(0x1, json.dumps({"command": command, "message_id": str(self.mid), "args": args}).encode())
        return self.mid

    def call(self, command, timeout=60, **args):
        mid = self.send(command, **args)
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = self.recv()
            if m.get("message_id") == str(mid):
                if "error_code" in m: raise RuntimeError(f"{command}: {m}")
                return m
        raise TimeoutError(command)

if __name__ == "__main__":
    ws = WS()
    info = ws.recv()
    print("Server:", info.get("server_version"), "| Meldung-Schlüssel:", sorted(info.keys())[:12])
    cmd = sys.argv[1]; args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = ws.call(cmd, **args)
    print(json.dumps(r, ensure_ascii=False)[:3000])
