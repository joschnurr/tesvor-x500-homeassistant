import socket, struct, time, re, sys, os
def enc(s): b=s.encode(); return struct.pack('>H',len(b))+b
def pkt(t,body):
    rl=len(body); out=bytes([t])
    while True:
        d=rl%128; rl//=128; out+=bytes([d|0x80 if rl else d])
        if not rl: break
    return out+body
s=socket.create_connection((os.getenv('MQTT_HOST','127.0.0.1'),int(os.getenv('MQTT_PORT','1883'))),timeout=5)
s.sendall(pkt(0x10, enc('MQTT')+bytes([4,0x02])+struct.pack('>H',60)+enc('claude-rxwatch'))); s.recv(4)
s.sendall(pkt(0x82, struct.pack('>H',1)+enc('tesvor/x500/#')+bytes([0]))); s.settimeout(20)
buf=b''; ansi=re.compile(r'\x1b\[[0-9;]*m'); last=0
while True:
    try: buf+=s.recv(65536)
    except socket.timeout:
        s.sendall(pkt(0xC0,b'')); continue
    i=0
    while i<len(buf):
        t=buf[i]; j=i+1; rl=0; m=1
        while True:
            d=buf[j]; j+=1; rl+=(d&127)*m; m*=128
            if not d&128: break
        if j+rl>len(buf): break
        body=buf[j:j+rl]; i=j+rl
        if t>>4==3 and not t&1:
            tl=struct.unpack('>H',body[:2])[0]; topic=body[2:2+tl].decode(); pay=ansi.sub('',body[2+tl:].decode(errors='replace')).replace('\n',' ')
            if topic.endswith('/debug') and '<<<' in pay and time.time()-last>30:
                print(f"{time.strftime('%H:%M:%S')} EMPFANG {pay[pay.index('<<<'):][:120]}", flush=True); last=time.time()
            elif topic.endswith('/sensor/state/state') or topic.endswith('/status'):
                print(f"{time.strftime('%H:%M:%S')} {topic.split('/x500/')[-1]} = {pay[:60]}", flush=True)
    buf=buf[i:]
