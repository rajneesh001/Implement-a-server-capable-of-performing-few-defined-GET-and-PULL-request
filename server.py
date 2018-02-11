#!/usr/bin/python

# nesessary imports
# Author Rajneesh
#Craeted on
import socket
import sys
import json
import time

from urlparse import urlparse
from thread import *

# global variables
HOST = ''
PORT = 8081
CONN = {}
TIME = {}


# method to route according to request
def router(client_soc, client_addr):

    data = client_soc.recv(1024)           #receive data from client
    string = bytes.decode(data)                 #decode it to string

    # determine request method
    request_method = string.split(' ')[0]
    if request_method == 'GET':
        route = string.split(' ')
        route = route[1]
        url = urlparse(route)
        
        if url.path == '/api/request':
            newconnection(client_soc, client_addr, url)
        elif url.path == '/api/serverStatus':
            serverstatus(client_soc, client_addr)
       else:
           welcome(client_soc)
           
   else:
        client_soc.send('\n')
        client_soc.send('Wrong request method, only GET is supported.')
        client_soc.close()
           
                      
      if request_method == 'PUT':
        route = string.split(' ')
        route = route[1]
        
        url = urlparse(route)        
           
        if url.path == '/api/kill':
            killconnection(client_soc, client_addr, url)
        else:
            welcome(client_soc)

    else:
        client_soc.send('\n')
        client_soc.send('Wrong request method, only PUT is supported.')
        client_soc.close()

    return


def newconnection(client_soc, client_addr, url):
    query = url.query
    query_components = dict(qc.split("=") for qc in query.split("&"))

    # check if url has required query parameter and connId is not already running in server
    if 'connId' and 'timeout' in query_components:

        #get query parameters
        conn = query_components['connId']
        timeout = int(query_components['timeout'])

        if conn not in CONN:
            #get current time
            curr_time = int(time.time())

            #save client socket and running time in dict
            CONN[conn] = client_soc
            TIME[conn] = curr_time + timeout

            # response
            message = json.dumps({"status" : "OK"})
            header = {
                        'Content-Type': 'application/json; charset=utf8',
                        'Content-Length': len(message),
                        'Connection': 'close',
                    }

            header = ''.join('%s: %s\n' % (k, v) for k, v in \
                                            header.iteritems())

            time.sleep(float(timeout))

            if conn in CONN:
                protocol = 'HTTP/1.1'
                status = '200'
                status_text = 'OK'

                client_soc.send('%s %s %s' % (protocol, status, \
                                                        status_text))
                client_soc.send('\n')
                client_soc.send(header)
                client_soc.send('\n')
                client_soc.send(message)
                client_soc.close()

                # pop client from running client dict if availale
                CONN.pop(conn, None)
                TIME.pop(conn, None)

        else:

            # handle in case of bad request or error
            message = json.dumps({"errors": [{"code": 403,"message": "Request with connId already running"}]})
            code = (403, 'Forbidden')
            error(client_soc, message, code)

    else:

        # handle in case of bad request or error
        message = json.dumps({"errors": [{"code": 400,"message": "Bad request or querry."}]})
        code = (400, 'Bad Request')
        error(client_soc, message, code)

    return

def serverstatus(client_soc, client_addr):

    #get current time
    curr_time = int(time.time())
    running_req = {}

    # ittirate over dict keys - connId, substract req termination time from current time to get remaining time
    for i in CONN.keys():
        running_req[i] = str(TIME[i] - curr_time)

    message = json.dumps(running_req)
    header = {
                'Content-Type': 'application/json; charset=utf8',
                'Content-Length': len(message),
                'Connection': 'close',
            }

    header = ''.join('%s: %s\n' % (k, v) for k, v in \
                                    header.iteritems())

    protocol = 'HTTP/1.1'
    status = '200'
    status_text = 'OK'

    client_soc.send('%s %s %s' % (protocol, status, \
                                            status_text))
    client_soc.send('\n')
    client_soc.send(header)
    client_soc.send('\n')
    client_soc.send(message)
    client_soc.close()

    return

def killconnection(client_soc, client_addr, url):

    # get req query param
    query = url.query
    query_components = dict(qc.split("=") for qc in query.split("&"))

    # If query has connId and connection requested is running
    if 'connId' in query_components:
        conn = query_components['connId']
        if conn in CONN and TIME:
            conn_soc = CONN[conn]

            killit(conn_soc)          # kills the connection at socket fiven

            CONN.pop(conn, None)
            TIME.pop(conn, None)

            message = json.dumps({"status": "OK"})
            header = {
                        'Content-Type': 'application/json; charset=utf8',
                        'Content-Length': len(message),
                        'Connection': 'close',
                    }

            header = ''.join('%s: %s\n' % (k, v) for k, v in \
                                            header.iteritems())
            protocol = 'HTTP/1.1'
            status = '200'
            status_text = 'OK'

            client_soc.send('%s %s %s' % (protocol, status, \
                                                    status_text))
            client_soc.send('\n')
            client_soc.send(header)
            client_soc.send('\n')
            client_soc.send(message)
            client_soc.close()

        else:
            # handle in case of bad request or error
            status = 'Invalid Connection Id: %s' %(conn)
            message = json.dumps({"status": status})
            code = (400, 'Forbidden')
            error(client_soc, message, code)

    else:
        # handle in case of bad request or error
        message = json.dumps({"errors": [{"code": 400,"message": "Bad request or querry."}]})
        code = (400, 'Bad Request')
        error(client_soc, message, code)

    return


# welcome and fallback handler, when url or query is wrong
def welcome(client_soc):
    message = 'Welcome!! We support three API requests as follows..'
    message += '1. new connection - method = GET, path = /api/request with query = connId=<connection id>&timeout=<time>'
    message += '2. server status - method = GET, path = /api/serverStatus'
    message += '3. kill connection - method = GET, path = /api/kill'

    header = {
                'Content-Type': 'text/plain; charset=utf8',
                'Content-Length': len(message),
                'Connection': 'close',
            }
    header = ''.join('%s: %s\n' % (k, v) for k, v in \
                                    header.iteritems())
    protocol = 'HTTP/1.1'
    status = '200'
    status_text = 'OK'

    client_soc.send('%s %s %s' % (protocol, status, \
                                            status_text))

    client_soc.send('\n')
    client_soc.send(header)
    client_soc.send('\n')
    client_soc.send(message)
    client_soc.close()
    return

def error(client_soc, message, code):

    message = message
    header = {
                'Content-Type': 'application/json; charset=utf8',
                'Content-Length': len(message),
                'Connection': 'close',
            }

    header = ''.join('%s: %s\n' % (k, v) for k, v in \
                                    header.iteritems())

    protocol = 'HTTP/1.1'
    status = code[0]
    status_text = code[1]

    client_soc.send('%s %s %s' % (protocol, status, \
                                            status_text))
    client_soc.send('\n')
    client_soc.send(header)
    client_soc.send('\n')
    client_soc.send(message)
    client_soc.close()
    return


def killit(client_socket):

    message = json.dumps({"status": "KILLED"})
    header = {
                'Content-Type': 'application/json; charset=utf8',
                'Content-Length': len(message),
                'Connection': 'close',
            }

    header = ''.join('%s: %s\n' % (k, v) for k, v in \
                                    header.iteritems())
    protocol = 'HTTP/1.1'
    status = '200'
    status_text = 'OK'

    client_socket.send('%s %s %s' % (protocol, status, \
                                            status_text))
    client_socket.send('\n')
    client_socket.send(header)
    client_socket.send('\n')
    client_socket.send(message)
    client_socket.close()

    return


if __name__ == "__main__":
    # start server and accept requests
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print('socket sucessfully created')
            print('Press Ctrl+C to shut down.')

        except socket.error as error:
            print "socket creation failed with error %s" %(err)
            sys.exit()

        s.bind((HOST, PORT))
        s.listen(10)

        try:
            while True:
                client_soc, client_addr = s.accept()

                print 'New request from', client_addr
                start_new_thread(router ,(client_soc,client_addr))

        except KeyboardInterrupt:
            print 'Ctrl+C pressed... Server will shut down.'
        except Exception, err:
            print 'Exception caught: %s\nClosing...' % err

        print 'Shutting down server.....'
        s.close()
        sys.exit()