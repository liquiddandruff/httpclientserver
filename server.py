#!/usr/bin/env python3
import re, os
from socket import *

SCRIPT_LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
SERVER_PORT = 12000

serverSocket = socket(AF_INET, SOCK_STREAM)
# Reuse local addresses
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('localhost', SERVER_PORT))
# Maximum 10 clients
serverSocket.listen(10)

def formHeaderResponse():
    response = ("HTTP/1.1 200 TRUE\r\n\r\n")
    return response.encode('utf-8')

def formBinaryResponse(bfLength, bfName):
    # HTTP protocol uses CRLF type endlines
    response = ("HTTP/1.1 200 OK\r\n"
                "Accept-Ranges: bytes\r\n"
                "Keep-Alive: timeout=10, max=100\r\n"
                "Connection: Keep-Alive\r\n"
                # Set lengthm, content-type, disposition to faciliate binary download
                "Content-Length: " + str(bfLength) + "\r\n"
                "Content-Type: application/octet-stream\r\n"
                # HTTP protocol expects two endlines as header termination
                "Content-Disposition: attachment; filename=" + bfName + "\r\n\r\n")
    print(response)
    return response.encode('utf-8')

def form404Response(rf):
    html = ("<center>Error 404: File not found!<br>"
            "You have requested for a non existing file: <b>" + rf + "</b><br><br>"
            "Please try another file</center>")
    response = ("HTTP/1.1 404 Not Found\r\n"
                "Keep-Alive: timeout=10, max=100\r\n"
                "Content-Length: " + str(len(html)) + "\r\n"
                "Content-Type: text/html\r\n\r\n")
    return (response + html).encode('utf-8')

def formHomePageResponse():
    html = ("<center><b>Welcome!</b><br>"
            "You have reached Steven Huang's web server<br><br>"
            "Enjoy your stay!</center>")
    response = ("HTTP/1.1 200 OK\r\n"
                "Keep-Alive: timeout=10, max=100\r\n"
                "Content-Length: " + str(len(html)) + "\r\n"
                "Content-Type: text/html\r\n\r\n")
    return (response + html).encode('utf-8')


print("Server is listening...")

try:
    while True:
        connectionSocket, addr = serverSocket.accept()
        request = connectionSocket.recv(1024).decode('utf-8')
        if not request:
            continue
        print("\n:RECV REQUEST\n" + request + "\n:END REQUEST\n")

        # Get the request type and file
        try:
            requestType = request.split()[0]
            requestedFile = request.split()[1]
            if requestType != 'GET' and requestType != 'HEAD':
                raise Exception;
        except:
            print("\nMalformed HTTP request; ignoring..")
            continue

        if requestedFile == "/":
            connectionSocket.send(formHomePageResponse())
            continue

        print("\nRequested file \"" + requestedFile + "\"")
        try:
            # Open file in read-only, binary mode, trim /
            binaryFile = open(os.path.join(SCRIPT_LOCATION, requestedFile[1:]), 'rb')
            print(" FOUND AT " + SCRIPT_LOCATION + '\n')
            if requestType == 'GET':
                data = binaryFile.read().decode('utf-8')
                connectionSocket.send(formBinaryResponse(len(data), requestedFile))
                for i in range(0, len(data)):
                    connectionSocket.sendall(data[i].encode('utf-8'))
                    print("Sending: " + data[i])
            else:
                connectionSocket.send(formHeaderResponse())
            binaryFile.close()
        except ConnectionError as e:
            print(str(e) + ": Client exploded, RIP")
        except IOError:
            print(" NOT FOUND at " + SCRIPT_LOCATION + '\n')
            connectionSocket.send(form404Response(requestedFile))
        finally:
            connectionSocket.close()
except KeyboardInterrupt:
    print("\n^C Detected: Terminating gracefully")
finally:
    print("Server socket closed")
    serverSocket.close()
