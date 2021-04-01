#!/usr/bin/env python
# -*- coding: utf-8 -*-

# modbus_thread
# start a thread for polling a set of registers, display result on console
# exit with ctrl+c

import time
from threading import Thread, Lock
#Modbus Matters
import argparse

import rospy
import roslib
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist 

from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
from pdb import set_trace as bp
import numpy as np
import json

# set global
#data related to server
DATA_FROM_HOLDING = []
DATA_TO_HOLDING = []

DATA_FROM_COIL = []
DATA_TO_COIL = []

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
MDS_ADDR_R = {'addr_start_holding_R':0,
        'addr_num_holding_R': 8,
        'addr_start_coil_R':0,
        'addr_num_coil_R':8}

MDS_ADDR_W = {'addr_start_holding_W':0,
          'addr_num_holding_W':6,
          'addr_start_coil_W':0,
          'addr_num_coil_W':8}
MODBUS_SPEC = {'SERVER_HOST':"192.168.1.10",
               'SERVER_PORT':502}

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
pub_freq = 25.0
rospy.init_node('cmd_vel_listener_rpm_publisher')
rate = rospy.Rate(pub_freq)

# modbus polling thread
#def modbus_polling_thread():
# start polling thread
#tp = Thread(target=modbus_polling_thread)
#tp.daemon = True
#tp.start()

def callback(msg):
    global DATA_TO_HOLDING,DATA_FROM_HOLDING,DATA_FROM_COIL,DATA_TO_COIL
    global start_addr,test_signal_coil,test_signal_holding
    global addr_num
    vx = msg.linear.x*1000;
    vy = msg.linear.y*1000;
    vz = msg.linear.z*1000;
    rx = msg.angular.x*1000;
    ry = msg.angular.y*1000;
    rz = msg.angular.z*1000;
    DATA_TO_HOLDING = [vx,vy,vz,rx,ry,rz]
    c = ModbusClient(host=MODBUS_SPEC['SERVER_HOST'], port=MODBUS_SPEC['SERVER_PORT'])
    ## polling loop
    # keep TCP open
    if not c.is_open():
        c.open()
    #print('DATA_TO_HOLDING = %s' % (DATA_TO_HOLDING))
    if DATA_TO_HOLDING is not None and len(DATA_TO_HOLDING) is not 0 :
        if c.write_multiple_registers(MDS_ADDR_W['addr_start_holding_W'],DATA_TO_HOLDING):
            print('write holding ok from addr %s with list %s' % (MDS_ADDR_W['addr_start_holding_W'],DATA_TO_HOLDING))
        else:
            print('write holding error from addr %s with list %s' % (MDS_ADDR_W['addr_start_holding_W'],DATA_TO_HOLDING))
    else:
        print('holding data missing with %s with desired len %s' % (DATA_TO_HOLDING,MDS_ADDR_W['addr_num_holding_W']))
    time.sleep(0.1)
    # read data from serve(holding & coil)
    #DATA_FROM_HOLDING = c.read_holding_registers(MDS_ADDR_R['addr_start_holding_R'], MDS_ADDR_R['addr_num_holding_R'])
    #DATA_FROM_COIL = c.read_coils(MDS_ADDR_R['addr_start_coil_R'],MDS_ADDR_R['addr_num_coil_R'])
    #print('Holding %s COil %s',DATA_FROM_HOLDING,DATA_FROM_COIL)
    #print('reading form mds slave')
    #if DATA_FROM_HOLDING:
    #    with regs_lock:
    #        print('with regs_lock_holding')
    #        holding_payload_to_ros = {}     
    #if DATA_FROM_COIL:
    #    #insert data from coil register
    #    coil_payload_to_ros = {}
    #    for y in range(0,MDS_ADDR_R['addr_num_coil_R']):
    #        coil_payload_to_ros[str(MDS_ADDR_R['addr_start_coil_R']+y)] = DATA_FROM_COIL[y]
    #    input_coil = json.dumps(coil_payload_to_ros) 
    #else:
    #    print('listenning to holding register fail')

#while True:
if __name__ == '__main__':
    try:
        print('waiting for subscribe /cmd_vel')
        rospy.Subscriber("/cmd_vel",Twist, callback)
        rospy.spin()
    except rospy.ROSInterruptException:
	pass
    time.sleep(2)

