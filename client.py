#!/usr/bin/env python3
import re, os, sys, time
from socket import *

TIME_OUT_LIMIT = 3
SCRIPT_LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
CONTENT_LENGTH_HEADER = "Content-Length: "
CRLF = '\r\n'

def formRequest(req_type, req_name):
    response = (req_type + " /" + req_name + " HTTP/1.1"+2*CRLF)
    print("Sending request: " + repr(response))
    return (response).encode('utf-8')

def getContentLength(headers):
    leftIndex = headers.find(CONTENT_LENGTH_HEADER)
    if leftIndex == -1:
        return -1
    else:
        leftIndex += len(CONTENT_LENGTH_HEADER)
    rightIndex = headers.find(CRLF, leftIndex)
    return int(headers[leftIndex:rightIndex])

def getHeaders():
    rcvBuffer = ""
    httpHeaders = ""
    while True:
        response = clientSocket.recv(12).decode('utf-8')
        if not response:
            continue
        rcvBuffer += response;
        lastCRLFindex = rcvBuffer.rfind(CRLF)
        if lastCRLFindex != -1:
            # We assume valid HTTP responses (2 CRLFs as header termination)
            for line in rcvBuffer[:lastCRLFindex + 2].splitlines(True):
                httpHeaders += line
                if line == CRLF and httpHeaders[-2:] == CRLF:
                    return httpHeaders, rcvBuffer[2 + lastCRLFindex:]
            rcvBuffer = rcvBuffer[2 + lastCRLFindex:]

def getContent(rcvBuffer, cl):
    contentBuffer = rcvBuffer
    while True:
        content = clientSocket.recv(12).decode('utf-8')
        if not content:
            continue
        contentBuffer += content
        if len(contentBuffer) >= cl:
            return contentBuffer

try:
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    file_name = sys.argv[3]
    request_type = sys.argv[4].upper()
    if request_type != 'GET' and request_type != 'HEAD':
        raise Exception
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.settimeout(TIME_OUT_LIMIT)
    clientSocket.connect((server_host, server_port))
except ConnectionRefusedError:
    print("Connection refused. Is the server up?")
    sys.exit();
except:
    print("""Wrong arguments. Usage:
    client.py server_host server_port filename GET
    client.py server_host server_port filename HEAD""")
    sys.exit();

print("Connected to " + server_host + ":" + str(server_port) + "\n")
clientSocket.send(formRequest(request_type, file_name))
print("Request sent. Waiting for response...\n")

try:
    headers, rcvBuffer = getHeaders()
    responseCode = headers.split()[1]

    if responseCode == '200':
        if request_type == 'GET':
            try:
                print("Response code 200 received: " + repr(headers)  + "\nDownloading file...")
                content = getContent(rcvBuffer, getContentLength(headers))
                print("File successfully downloaded\n")
            except timeout:
                print("File partially downloaded due to timeout; writing file anyways")
            finally:
                with open(os.path.join(SCRIPT_LOCATION, "DL_" + file_name), 'wb') as binaryFile:
                    binaryFile.write(content.encode('utf-8'))
        elif request_type == 'HEAD':
            print("Response code 200 (TRUE) received: " + repr(headers) + "\n")
    elif responseCode == '404':
        print("Response code 404 received: " + repr(headers) + "\n")
except timeout:
    print("Timed out. Exiting")
except (ValueError, IndexError):
    print("\Received malformed headers. Exiting")
except KeyboardInterrupt:
    print("\n^C Detected. Terminating gracefully")
finally:
    print("Client socket closed")
    clientSocket.close()
