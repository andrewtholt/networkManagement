#!/usr/bin/env python3

import subprocess
import sqlite3
import sys
import threading
import time
import datetime
import queue
import signal
import os

import paho.mqtt.client as mqtt

conn = sqlite3.connect('node.db')

c = conn.cursor()


workQueue=queue.Queue(10)

exitFlag = False
queueLock = threading.Lock()

connected = False

def handler(signum, frame):
    global exitFlag
    print('Signal handler called with signal', signum)
    exitFlag=True

# tst = subprocess.run(["ls","-ltr"], universal_newlines=True,stdout=subprocess.PIPE)
def on_connect(client, userdata, flags, rc):
    global connected
    connected=True
    print("Connected")

def process_data(threadName, q):
    global exitFlag
    mqttBroker = "192.168.10.124"
    mqttPort = 1883

    while not exitFlag:
        print("Process")
        queueLock.acquire()
        if not workQueue.empty():
            print("Process In")
            data = q.get()

            queueLock.release()
            print ("%s processing %s" % (threadName, data))

            stuff = data.split(':')
            print(stuff)

            cause      = stuff[0]
            ip_address = stuff[1]
            name       = stuff[2]
            state      = stuff[3]

            mqttClient = mqtt.Client()
            mqttClient.on_connect = on_connect

            print("MQTT connecting ...")
            mqttClient.connect(mqttBroker, mqttPort, 60)

            while not connected:
                print("Waiting ....")
                time.sleep(0.1)
                mqttClient.loop()
            print("MQTT connected ")

            topic = "/test/monitor/"

            if name == "":
                topic += ip_address
            else:
                tmp = name.split('.')
                topic += tmp[0]

            topic += "/"

            # TODO command line flag to make payload JSON
            # TODO If state is 'down' check by some other means (ping etc)

            mqttClient.publish(topic + 'event_time',payload='{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
            mqttClient.publish(topic + 'cause',payload=cause)
            mqttClient.publish(topic + 'state',payload=state)

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
      print ("Starting " + self.name)
      process_data(self.name, self.q)

      print ("Exiting " + self.name)


def main(subNet):
    global exitFlag
    signal.signal(signal.SIGINT, handler)

    thread = myThread(1,"TEST", workQueue)
    thread.start()

    cmd= "fing --silent " + subNet + "/24 -o log,csv"
    cmdList = cmd.split(" ")

    tst = subprocess.Popen(cmdList, universal_newlines=True,stdout=subprocess.PIPE)
    while not exitFlag:
        output = tst.stdout.readline()
        print(output)
        fred = output.splitlines()

    #    print(fred)

        for data in fred:
            #        print(data)

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

            sqlCmd = 'select count(*),state,notify from node where ip_address = "'+ ip_address + '";'

        #    print(sqlCmd)

            for res in c.execute( sqlCmd ):
                #        print(res)
                resultCount=res[0]
                resultState=res[1]
                resultNotify=res[2]

                ticks = time.time()

                if resultCount == 0:
                    print("No match, insert and alert")
                    sqlCmd = 'insert into node '
                    sqlCmd += '(time_stamp,state,ip_address,unknown,name,mac_address,maker,event_time) '
                    sqlCmd += "values('" + time_stamp + "','" + state + "','"  + ip_address 
                    sqlCmd += "','" + unknown + "','" + name + "','"  + mac_address
                    sqlCmd += "','" + maker + "'," + str(int(ticks)) + ");"

                    print(sqlCmd)

                    c.execute(sqlCmd)
                    conn.commit()

                    dataOut = "NEW:" + ip_address + ":" + name +":" + state 
                    workQueue.put(dataOut)
                else:
                    print("Match, check state")
                    if resultState == state:
                        print("No Change in state")
                    else:
                        print("State change, alert and update db")

                        sqlCmd = "update node set state = '" + state + "',event_time =" + str(int(ticks)) + " where ip_address='" + ip_address + "';"
                        print(sqlCmd)
                        c.execute(sqlCmd)
                        conn.commit()

                        if resultNotify == "YES":
                            dataOut = "STATE:" + ip_address + ":" + name +":" + state 
                            workQueue.put(dataOut)


if len(sys.argv) == 2:
    print(sys.argv[1])
    main(sys.argv[1])
else:
    print("Usage: monitor.py <subnet address>")

