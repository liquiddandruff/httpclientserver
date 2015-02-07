#!/usr/bin/env python3
import re, os, sys, time
from socket import *

SECONDS_TO_WAIT = 1
SCRIPT_LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def formRequest(req_type, req_name):
    response = (req_type + " /" + req_name + " HTTP/1.1\r\n")
    return (response).encode('utf-8')

try:
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    file_name = sys.argv[3]
    request_type = sys.argv[4].upper()
    if request_type != 'GET' and request_type != 'HEAD':
        raise Exception
except:
    print("""Wrong arguments. Usage:
    client.py server_host server_port filename GET
    client.py server_host server_port filename HEAD""")
    sys.exit();

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((server_host, server_port))
clientSocket.send(formRequest(request_type, file_name))

print("Request sent. Waiting for response from server...")

try:
    t1 = time.clock()

    rcvBuffer = ""
    rcvdResponse = False
    httpHeadersParsed = False
    headers = []
    while True:
        if (not rcvdResponse and time.clock() - t1 > SECONDS_TO_WAIT):
            print("Timed out, exiting..")
            break
        response = clientSocket.recv(12).decode('utf-8')
        if not response:
            continue
        rcvdResponse = True
        print("\n:RECV RESPONSE\n" + response + "\n:END RESPONSE\n")

        try:
            rcvBuffer += response;
            lastBreak = rcvBuffer.rfind('\r\n')
            if not httpHeadersParsed and lastBreak != -1:
                for line in rcvBuffer[:lastBreak].split('\r\n'):
                    if line == '\r\n' and headers.index([len(headers)]) == '\r\n':
                        httpHeadersParsed = True
                    headers.append(line)
                print("buffer: " +rcvBuffer + "\nheaders: " +str(headers))
                rcvBuffer = rcvBuffer[2 + lastBreak:]
            responseCode = headers[0].split()[1]
            print("response: " + responseCode)
        except IndexError:
            continue

        if not httpHeadersParsed:
            continue

        print("Headerse parsed")
        if responseCode == '200':
            if request_type == 'GET':
                binaryFile = open(os.path.join(SCRIPT_LOCATION, "DL_" + file_name), 'wb')
            elif request_type == 'HEAD':
                print("Received TRUE")
        elif responseCode == '404':
            print("Received 404")


except KeyboardInterrupt:
    print("\n^C Detected: Terminating gracefully")
finally:
    print("Client socket closed")
    clientSocket.close()
