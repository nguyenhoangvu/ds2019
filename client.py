from __future__ import print_function
import random
import socket
import sys
import thread
import time
import xmlrpclib

END = "#&*END_OF_HTTP_MESSAGE*$#"

def handle(conn):
    request = conn.recv(4096)
    cmd = request.split(" ", 2)[0]
    if cmd != "GET" and cmd != "POST":
        # Commands other than GET and POST are not supported
        conn.close()
        return

    # Identify where we wanna go
    # GET http://hostname[:port][url] HTTP/1.1\n
    cmd, url, rest = request.split(" ", 2)
    host = url.replace("http://", "", 1)
    url = ""
    if host.find(":") != -1:
        host, port = host.split(":", 1)
        try:
            port, url = port.split("/", 1)
            port = int(port)
        except ValueError:
            port = 80
    else:
        host, url = host.split("/", 1)
        port = 80
    url = "/" + url

    print("* Proxy: %s %s:%s%s" % (cmd, host, port, url))
    while 1:
        time.sleep(0.5 + random.random())
        try:
            server.init_request(cmd, host, port, url, xmlrpclib.Binary(rest))
        except: # server busy
            continue
        break

    # Read segment starting at 'i' from RPC server
    i = 0
    while 1:
        time.sleep(0.5 + random.random())
        try:
            data = server.read_request(cmd, host, port, url, i)
            data = [d.data for d in data]
        except: # server busy
            continue
        if not data:
            continue
        if data[0] == END:
            break
        try:
            conn.sendall("".join(data))
            i += len(data)
        except: # broken connection
            break
    conn.close()

requests = {}

host = "" # empty string = localhost
port = 8000
if len(sys.argv) >= 2:
    port = int(sys.argv[1])

rpc_host = "localhost"
rpc_port = 9000

proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy.bind((host, port))
proxy.listen(100) # allow 100 browser requests at the same time

rpc = "http://%s:%s" % (rpc_host, rpc_port)
server = xmlrpclib.ServerProxy(rpc)

print("Proxy server listening on port %s." % port)
try:
    while 1:
        conn, addr = proxy.accept()
        thread.start_new_thread(handle, (conn,))
except KeyboardInterrupt:
    print("Exiting.")
    proxy.close()
