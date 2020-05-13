#!/usr/bin/env python3

import subprocess
import sqlite3
import sys
import threading
import time
import queue
import signal
import os

conn = sqlite3.connect('node.db')

c = conn.cursor()


workQueue=queue.Queue(10)

exitFlag = False
queueLock = threading.Lock()

def handler(signum, frame):
    global exitFlag
    print('Signal handler called with signal', signum)
    exitFlag=True

# tst = subprocess.run(["ls","-ltr"], universal_newlines=True,stdout=subprocess.PIPE)

def process_data(threadName, q):
   global exitFlag
   while not exitFlag:
      queueLock.acquire()
      if not workQueue.empty():
         data = q.get()
         queueLock.release()
         print ("%s processing %s" % (threadName, data))
      else:
         queueLock.release()
         # 
         # send somewhare else
         #
         time.sleep(0.1)

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
            
                if resultCount == 0:
                    print("No match, insert and alert")
                    sqlCmd = 'insert into node '
                    sqlCmd += '(time_stamp,state,ip_address,unknown,name,mac_address,maker) '
                    sqlCmd += "values('" + time_stamp + "','" + state + "','"  + ip_address 
                    sqlCmd += "','" + unknown + "','" + name + "','"  + mac_address
                    sqlCmd += "','" + maker + "');"
            
    #                print(sqlCmd)
            
                    c.execute(sqlCmd)
                    conn.commit()

                    workQueue.put("NEW:" + ip_address + ":" + state )
                else:
                    print("Match, check state")
                    if resultState == state:
                        print("No Change in state")
                    else:
                        print("State change, alert and update db")
    
                        sqlCmd = "update node set state = '" + state + "' where ip_address='" + ip_address + "';"
                        print(sqlCmd)
                        c.execute(sqlCmd)
                        conn.commit()

                        if resultNotify == "YES":
                            workQueue.put("STATE:" + ip_address + ":" + state )
            
            
if len(sys.argv) == 2:
    print(sys.argv[1])
    main(sys.argv[1])
else:
    print("Usage: monitor.py <subnet address>")


