#!/usr/bin/env python3
import re, os, sys, time
from socket import *

SECONDS_TO_WAIT = 1
SCRIPT_LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
CONTENT_LENGTH_HEADER = "Content-Length: "

def formRequest(req_type, req_name):
    response = (req_type + " /" + req_name + " HTTP/1.1\r\n")
    return (response).encode('utf-8')

def getContentLength(headers):
    leftIndex = headers.find(CONTENT_LENGTH_HEADER)
    if leftIndex == -1:
        return -1
    else:
        leftIndex += len(CONTENT_LENGTH_HEADER)
    rightIndex = headers.find('\r\n', leftIndex)
    return int(headers[leftIndex:rightIndex])

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

print("Request sent. Waiting for response...")

try:

    rcvBuffer = ""

    httpHeaders = ""
    httpHeadersParsed = False
    tSinceLastResponse = time.clock()
    while not httpHeadersParsed:
        if (time.clock() - tSinceLastResponse > SECONDS_TO_WAIT):
            print("Timed out, exiting..")
            break
        response = clientSocket.recv(12).decode('utf-8')
        if not response:
            continue
        tSinceLastResponse = time.clock()
        print("\n:RECV RESPONSE\n" + repr(response) + "\n:END RESPONSE\n")

        rcvBuffer += response;
        lastBreak = rcvBuffer.rfind('\r\n')
        if not httpHeadersParsed and lastBreak != -1:
            for line in rcvBuffer[:lastBreak + 2].splitlines(True):
                if line == '\r\n' and httpHeaders[-2:] == '\r\n':
                    httpHeadersParsed = True
                httpHeaders += line
            rcvBuffer = rcvBuffer[2 + lastBreak:]
        print("buffer: " + repr(rcvBuffer) + "\nheaders: " + repr(httpHeaders))
        print("httpHeadersParsed: " + str(httpHeadersParsed))

    responseCode = httpHeaders.split()[1]

    if responseCode == '200':
        if request_type == 'GET':
            contentBuffer = rcvBuffer
            contentLength = getContentLength(httpHeaders)
            contentParsed = False
            tSinceLastResponse = time.clock()
            while not contentParsed:
                if (time.clock() - tSinceLastResponse > SECONDS_TO_WAIT):
                    print("Timed out, exiting..")
                    break
                content = clientSocket.recv(12).decode('utf-8')
                if not content:
                    continue
                tSinceLastResponse = time.clock()
                print("\n:RECV CONTENT\n" + repr(content) + "\n:END CONTENT\n")

                contentBuffer += content
                contentParsed = True if len(contentBuffer) >= contentLength else False
            print("File downloaded")
            with open(os.path.join(SCRIPT_LOCATION, "DL_" + file_name), 'wb') as binaryFile:
                binaryFile.write(contentBuffer.encode('utf-8'))
        elif request_type == 'HEAD':
            print("Received TRUE", httpHeaders)
    elif responseCode == '404':
        print("Received 404", httpHeaders)
except KeyboardInterrupt:
    print("\n^C Detected: Terminating gracefully")
finally:
    print("Client socket closed")
    clientSocket.close()
