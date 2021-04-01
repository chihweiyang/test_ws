#!/usr/bin/env python
# -*- coding: utf-8 -*-

# modbus_thread
# start a thread for polling a set of registers, display result on console
# exit with ctrl+c

import time
from threading import Thread, Lock
#Modbus Matters
import argparse
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
from pdb import set_trace as bp
import numpy as np
import json

# set global
#data related to HMI
DATA_FROM_HMI_HOLDING = []
DATA_TO_HMI_HOLDING = []

DATA_FROM_HMI_COIL = []
DATA_TO_HMI_COIL = []

#data related to ros driver
DATA_TO_ROS_DRIVER_HOLDING = {}
DATA_FROM_ROS_DRIVER_HOLDING ={}
DATA_TO_ROS_DRIVER_COIL = {}
DATA_FROM_ROS_DRIVER_COIL = {}

# init a thread lock
#read lock
regs_lock = Lock()
msg_lock_w = Lock()
#read holding register from modbus slave without doing anything currently
MDS_ADDR_R = {'addr_start_holding_R':1,
        'addr_num_holding_R': 2,
        'addr_start_coil_R':32,
        'addr_num_coil_R':7}

MDS_ADDR_W = {'addr_start_holding_W':0,
          'addr_num_holding_W':4,
          'addr_start_coil_W':0,
          'addr_num_coil_W':2}
MODBUS_SPEC = {'SERVER_HMI_HOST':"192.168.1.10",
               'SERVER_HMI_PORT':502}

MQTT_SPEC = {'broker_url':'localhost',
             'broker_port':1883}

start_addr = 100
addr_num = 10
#read coiling register from modbus slave to do cancel goal
start_addr_coil = 100
addr_num_coil = 4
#write holding register to modbus slave
start_addr_w = 120
addr_num_w = 5
test_signal_coil = False
test_signal_holding = 0
class ratio_samplier:
    def __init__(self,sample_ratio):
        self.ratio_ = sample_ratio
        self.num_sample_ = np.uint64(0)
        self.num_pulses_ = np.uint64(0)
    def pull(self):
        self.num_pulses_ = self.num_pulses_ + 1
        if (1.0*self.num_sample_/self.num_pulses_)<self.ratio_:
            self.num_sample_ = self.num_sample_ + 1
            return True
        else:
            return False

# modbus polling thread
def modbus_polling_thread():
    global DATA_TO_HMI_HOLDING,DATA_FROM_HMI_HOLDING,DATA_FROM_HMI_COIL,DATA_TO_HMI_COIL
    global start_addr,test_signal_coil,test_signal_holding
    global addr_num
    c = ModbusClient(host=MODBUS_SPEC['SERVER_HMI_HOST'], port=MODBUS_SPEC['SERVER_HMI_PORT'])
    # polling loop
    while True:
        # keep TCP open
        if not c.is_open():
            c.open()
        # read data from hmi(holding & coil)
        DATA_FROM_HMI_HOLDING = c.read_holding_registers(MDS_ADDR_R['addr_start_holding_R'], MDS_ADDR_R['addr_num_holding_R'])
        # if read is ok, store result in regs (with thread lock synchronization)
        #time.sleep(0.)
        DATA_FROM_HMI_COIL = c.read_coils(MDS_ADDR_R['addr_start_coil_R'],MDS_ADDR_R['addr_num_coil_R'])
        print('Holding %s COil %s',DATA_FROM_HMI_HOLDING,DATA_FROM_HMI_COIL)
        print('reading form mds slave')
        if DATA_FROM_HMI_HOLDING:
            with regs_lock:
                print('with regs_lock_holding')
                #for demonstrate usage
                #DATA_FROM_HMI = list(DATA_FROM_HMI_HOLDING)
                ###
                holding_payload_to_ros = {}     
                #publish holding register data to ros driver
                if mqtt_client is not None:
                    #insert data from holding register
                    for x in range(0,MDS_ADDR_R['addr_num_holding_R']):
                        holding_payload_to_ros[str(MDS_ADDR_R['addr_start_holding_R']+x)] = DATA_FROM_HMI_HOLDING[x]
                         #transfer dict to string with json.dumps(payload_)
                    #print('holding payload to ros driver %s',sort_key(holding_payload_to_ros))
                    input_holding = json.dumps(holding_payload_to_ros)  
                    #transfer string to string with json.loads(input)
                    mqtt_client.publish(topic='DATA_TO_ROS_DRIVER_HOLDING_R', payload=input_holding, qos=2, retain=False)
                    time.sleep(0.05)
        if DATA_FROM_HMI_COIL:
            #insert data from coil register
            coil_payload_to_ros = {}
            for y in range(0,MDS_ADDR_R['addr_num_coil_R']):
                coil_payload_to_ros[str(MDS_ADDR_R['addr_start_coil_R']+y)] = DATA_FROM_HMI_COIL[y]
            input_coil = json.dumps(coil_payload_to_ros)
            #print('coil payload to ros driver %s',sort_key(coil_payload_to_ros))
            if mqtt_client is not None:
                mqtt_client.publish(topic='DATA_TO_ROS_DRIVER_COIL_R',payload=input_coil,qos=2,retain=False)
  
        else:
            print('listenning to holding register fail')

        #write data to hmi(holding & coil)
        with msg_lock_w:
            print('with msg_lock_coiling')
            print('DATA_TO_HMI_HOLDING %s',DATA_TO_HMI_HOLDING)
            if DATA_TO_HMI_HOLDING is not None and len(DATA_TO_HMI_HOLDING) is not 0 and len(DATA_TO_HMI_HOLDING) == MDS_ADDR_W['addr_num_holding_W']:
                print('SDSDASD %s',MDS_ADDR_W['addr_start_holding_W'])
                if c.write_multiple_registers(MDS_ADDR_W['addr_start_holding_W'],DATA_TO_HMI_HOLDING):
                    print('write holding ok from addr %s with list %s',MDS_ADDR_W['addr_start_holding_W'],DATA_TO_HMI_HOLDING)
                else:
                    print('write holding error from addr %s with list %s',MDS_ADDR_W['addr_start_holding_W'],DATA_TO_HMI_HOLDING)
            else:
                print('holding data missing with %s with desired len %s',DATA_TO_HMI_HOLDING,MDS_ADDR_W['addr_num_holding_W'])
            time.sleep(0.1)
            if DATA_TO_HMI_COIL is not None and len(DATA_TO_HMI_COIL) is not 0 and len(DATA_TO_HMI_COIL) == MDS_ADDR_W['addr_num_coil_W']:
                print(MDS_ADDR_W['addr_start_coil_W'])
                is_ok = c.write_multiple_coils(MDS_ADDR_W['addr_start_coil_W'],DATA_TO_HMI_COIL)
                if is_ok:
                    print('write coil ok from addr %s with list %s',MDS_ADDR_W['addr_start_coil_W'],DATA_TO_HMI_COIL)
                else:
                    print('write coil error from addr %s with list %s',MDS_ADDR_W['addr_start_coil_W'],DATA_TO_HMI_COIL)
            else:
                print('coil data missing with %s with desired len %s',DATA_TO_HMI_COIL,MDS_ADDR_W['addr_num_coil_W'])
            #write something to HMI 
        time.sleep(0.1)

# start polling thread
tp = Thread(target=modbus_polling_thread)
#set daemon: polling thread will exit if main thread exit
tp.daemon = True
tp.start()


# display loop (in main thread)

while True:
    # print regs list (with thread lock synchronization)
    '''
    with regs_lock:
        print('haha')
        time.sleep(1.0)
        #print('read holding data from modbus slave',DATA_FROM_HMI_HOLDING)
        #print('read holding data from modbus slave',DATA_FROM_HMI_COIL)
    '''
    time.sleep(0.2)
    # 1s before next print
