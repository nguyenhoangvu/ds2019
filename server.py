from __future__ import print_function
from SimpleXMLRPCServer import SimpleXMLRPCServer
import socket
import thread
import xmlrpclib

END = "#&*END_OF_HTTP_MESSAGE*$#"

def handle(cmd, host, port, url, rest):
    request = "%s %s:%s%s" % (cmd, host, port, url)
    try:
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # remote.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        remote.connect((host, port))
        remote.send("%s %s %s" % (cmd, url, rest))
        remote.settimeout(5)
        try:
            while 1:
                data = remote.recv(4096)
                if not data:
                    requests[request].append(END)
                    break
                requests[request].append(data)
        except socket.timeout:
            requests[request].append(END)
        remote.close()
    except Exception as e:
        print(e)
        requests[request].append(END)
        if remote:
            remote.close()

def init_request(cmd, host, port, url, rest):
    request = "%s %s:%s%s" % (cmd, host, port, url)
    print("*** RPC: %s" % request)
    if request not in requests:
        requests[request] = []
        thread.start_new_thread(handle, (cmd, host, port, url, rest.data))

def read_request(cmd, host, port, url, i):
    request = "%s %s:%s%s" % (cmd, host, port, url)
    if request not in requests:
        return ""
    r = requests[request]
    print("*** RPC: %s #%s/%s" % (request, i, len(r)-1))
    try:
        data = [r[i]]
    except IndexError:
        data = []
    if data:
        for d in r[i+1:]:
            if d == END:
                break
            data.append(d)
        data = [xmlrpclib.Binary(d) for d in data]
    return data

requests = {}
    
rpc_host = "localhost"
rpc_port = 9000

print("Accepting HTTP-over-RPC requests at %s:%s." % (rpc_host, rpc_port))
server = SimpleXMLRPCServer((rpc_host, rpc_port),
                            logRequests=False, allow_none=True)
server.register_introspection_functions()
server.register_multicall_functions()
server.register_function(init_request)
server.register_function(read_request)
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("Exiting.")
