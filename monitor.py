#!/usr/bin/env python3.7

import subprocess
import sqlite3
import sys
import threading
import time
import datetime
import queue
import signal
import os
import socket
from ping3 import ping
import getopt

import paho.mqtt.client as mqtt

conn = sqlite3.connect('node.db')

c = conn.cursor()

workQueue=queue.Queue(10)

exitFlag = False
queueLock = threading.Lock()

connected = False
verbose = False

def usage():
    print("Usage: monitor.py -h | -v -s <subnet address")

def checkNode(ip,port):

    if verbose:
        print("CHECKING",ip,port)

    state = "down"

    fail=True

    if port != 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((ip, port))
                state = "up"
                fail = False
            except:
                state = "down"
    
                fail = True

    if fail:
        res = ping(ip,timeout=1)
        res = ping(ip,timeout=2)

        if res == None:
            state = 'down'
        else:
            state = 'up'

    return state

def handler(signum, frame):
    global exitFlag
#    print('Signal handler called with signal', signum)
    exitFlag=True

# tst = subprocess.run(["ls","-ltr"], universal_newlines=True,stdout=subprocess.PIPE)
def on_connect(client, userdata, flags, rc):
    global connected
    connected=True
    if verbose:
        print("MQTT Connected")

def process_data(threadName, q):
    global exitFlag
    mqttBroker = "192.168.10.124"
    mqttPort = 1883

    count=1

    while not exitFlag:

        queueLock.acquire()
        if not workQueue.empty():
#            print("Process In")
            data = q.get()

            queueLock.release()
#            print ("%s processing %s" % (threadName, data))

            stuff = data.split(':')
#            print(stuff)

            cause      = stuff[0]
            ip_address = stuff[1]
            name       = stuff[2]
            state      = stuff[3]

            mqttClient = mqtt.Client()
            mqttClient.on_connect = on_connect

            if verbose:
                print("MQTT connecting ...")
            mqttClient.connect(mqttBroker, mqttPort, 60)

            while not connected:
                print("Waiting ....")
                time.sleep(0.1)
                mqttClient.loop()

            if verbose:
                print("MQTT connected ")

            topic = "/test/monitor/"

            if name == "":
                topic += ip_address
            else:
                tmp = name.split('.')
                topic += tmp[0]

            topic += "/"

            # TODO command line flag to make payload JSON

            if verbose:
                print( "Cause:" + topic + 'cause:' + cause )
                print( "State:" + topic + 'state:' + state )

            mqttClient.publish(topic + 'event_time',payload='{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
            mqttClient.publish(topic + 'cause',payload=cause)
            mqttClient.publish(topic + 'state',payload=state)

            if verbose:
                print("MQTT disconnecting")
            mqttClient.disconnect()
        else:
            queueLock.release()
            time.sleep(1)


class myThread (threading.Thread):
    def __init__(self, threadID, name, q):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.q = q
    def run(self):
      if verbose:
        print ("Thread Starting " + self.name)
      process_data(self.name, self.q)

      if verbose:
        print ("Thread exiting " + self.name)


def main(subNet):

    print("Verbose",verbose)
    global exitFlag
    signal.signal(signal.SIGINT, handler)

    thread = myThread(1,"TEST", workQueue)
    thread.start()

    cmd= "fing --silent " + subNet + "/24 -o log,csv"
    cmdList = cmd.split(" ")

    tst = subprocess.Popen(cmdList, universal_newlines=True,stdout=subprocess.PIPE)
    while not exitFlag:
        output = tst.stdout.readline()
        fred = output.splitlines()

        for data in fred:
            dataList = data.split(";")

            time_stamp = dataList[0]
            state = dataList[1]
            ip_address = dataList[2]
            unknown = dataList[3]
            name = dataList[4]
            mac_address = dataList[5]
            maker = dataList[6]

    #        print("time_stamp :" + time_stamp)
    #        print("state      :" + state)
    #        print("ip_address :" + ip_address)
    #        print("unknown    :" + unknown)
    #        print("name       :" + name)
    #        print("mac_address:" + mac_address)
    #        print("maker      :" + maker)

            sqlCmd = 'select count(*),state,notify,checkport from node where ip_address = "'+ ip_address + '";'

        #    print(sqlCmd)

            for res in c.execute( sqlCmd ):
                resultCount=res[0]
                resultState=res[1]
                resultNotify=res[2]
                checkport = res[3]

                ticks = time.time()

                if resultCount == 0:
                    if verbose:
                        print("No match, insert and alert")
                    sqlCmd = 'insert into node '
                    sqlCmd += '(time_stamp,state,ip_address,unknown,name,mac_address,maker,event_time) '
                    sqlCmd += "values('" + time_stamp + "','" + state + "','"  + ip_address 
                    sqlCmd += "','" + unknown + "','" + name + "','"  + mac_address
                    sqlCmd += "','" + maker + "'," + str(int(ticks)) + ");"

                    if verbose:
                        print(sqlCmd)

                    c.execute(sqlCmd)
                    conn.commit()

                    dataOut = "NEW:" + ip_address + ":" + name +":" + state 
                    workQueue.put(dataOut)
                else:
                    if verbose:
                        print("Match, check state")

                        print("oldState      ", resultState)
                        print("new State     ", state)

                    if resultState == state:
                        if verbose:
                            print("No Change in state")
                    else:
                        # TODO If state is 'down' check by some other means (ping etc)

                        state = checkNode(ip_address,checkport)

                        if verbose:
                            print("Checked State ", state)

                        if resultState != state:

                            if verbose:
                                print("State change, alert and update db")
    

                            sqlCmd = "update node set state = '" + state + "',time_stamp='" + time_stamp + "',event_time =" + str(int(ticks)) + " where ip_address='" + ip_address + "';"

                            if verbose:
                                print(sqlCmd)
                            c.execute(sqlCmd)
                            conn.commit()
    
                            if resultNotify == "YES":
                                dataOut = "STATE:" + ip_address + ":" + name +":" + state 
                                workQueue.put(dataOut)

def start():
    global verbose
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:v")
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-h':
            usage()
            sys.exit(2)
        elif o== '-s':
            subNet = a
        elif o == '-v':
            print("Verbose")

#    print(sys.argv[1])

    main( subNet )

start()

