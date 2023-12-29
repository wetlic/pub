from python_network_tools import device_connection_handler
from netmiko.ssh_exception import  NetMikoTimeoutException
from paramiko.ssh_exception import SSHException
from socket import gethostbyname, gaierror
from time import sleep
from datetime import datetime
import csv
import os
import netmiko
import yaml
import pprint

import logging
import re
import io
import argparse
import urllib3
import librenms_api
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
LIBRENMS_SERVER = "librenms.mgmt.local"
DEVICEIP = "172.29.180.107"

def setIntfSFP(connection, interface, switchOS, intfSFPTemp):
    printDebug ("NO", intfSFPTemp)
    if (intfSFPTemp.find("Fabric") > -1):
        intfSFP = "FEX"
    elif (intfSFPTemp.find("SFP-1000") > -1):
        intfSFP = "SFP 1G-Base-SR"
    elif (intfSFPTemp.find("10Gbase-SR") > -1):
        intfSFP = "SFP 10G-Base-SR"
    elif (intfSFPTemp.find("10GBase-SR") > -1):
        intfSFP = "SFP 10G-Base-SR"
    elif (intfSFPTemp.find("10Gbase-CU") > -1):
        intfSFP = "SFP 10G-Base-C"
    elif (intfSFPTemp.find("SFP-10GBase-SR") > -1):
        intfSFP = "SFP 10G-Base-SR"
    elif (intfSFPTemp.find("10/100/1000BaseTX") > -1):
        intfSFP = "Auto 1000BaseT"
    elif (intfSFPTemp.find("1000BaseSX") > -1):
        intfSFP = "SFP 1G-Base-SX"
    elif (intfSFPTemp.find("1000baseSX") > -1):
        intfSFP = "SFP 1G-Base-SX"
    elif (intfSFPTemp.find("SFP-H10GB-CU1M") > -1):
        intfSFP = "SFP 10G-Base-C1M"
    elif (intfSFPTemp.find("SFP-H10GB-CU3M") > -1):
        intfSFP = "SFP 10G-Base-C3M"
    elif (intfSFPTemp.find("SFP-H10GB-C") > -1):
        intfSFP = "SFP 10G-Base-C"
    elif (intfSFPTemp.find("1000base-T") > -1):
        intfSFP = "SFP 1G-Base-T"
    elif (intfSFPTemp.find("10/100BaseTX") > -1):
        intfSFP = "Auto 10/100BaseT"
    else:
        intfSFP = intfSFPTemp + " not known"
        if switchOS == "fex":
             sshCmd="sh interface "+interface+ "  transceiver | i length "
             printDebug("NO", "NEU NEU cmd {}  " .format(sshCmd))
             intfList = connection.send_command(sshCmd)


             printDebug("NO", "NEU NEU interfaceList {} type of {} " .format(intfList, type(intfList)))
             if (len(intfList) > -1):
                 buf = intfList.split("\n")
                 for entry in buf:
                     if entry.find("copper") > -1:
                          intfSFP = "SFP 10G-Base-C"
    return intfSFP

def getInterfaceASA(credentials,  interfaceList, switchName, switchOS, switchLocation, switchLocationNew):
    try:
        #connection = device_connection_handler.connect(switchName, "cisco_asa", credentials)
        switchNameRaw=switchName
       
        connection = device_connection_handler.connect(switchNameRaw, "cisco_asa", credentials)
        response = connection.send_command("show mode")
        if "Security context mode: multiple" in response:
            context_mode = True
        elif "Security context mode: single" in response:
            context_mode = False

        #print("context mode {}" .format(context_mode))
        if context_mode:
            connection.send_command("changeto context system")
        sshCmd="sh int ip brief | i up"

        #print("CMD : {}" .format(sshCmd))
        intfList = connection.send_command(sshCmd)
        #print("interfaceList {} type of {} " .format(intfList, type(intfList)))
        if (len(intfList) > -1):
            buf = intfList.split("\n")
            #print("buf {}" .format(buf))
            for entry in buf:
                intfEntries = re.split('\s+', entry)
                if intfEntries[0].find("Ethernet") > -1 or intfEntries[0].find("Management") > -1 :
                    intfName = intfEntries[0]
                    sshCmd="sh int " + intfName + " | i Interface"
                    intfSpec = connection.send_command(sshCmd)
                    intfSpecPos1=intfSpec.find('"')+1
                    intfSpecPos2=intfSpec.find('"',intfSpecPos1)

                    intfDescription=intfSpec[intfSpecPos1:intfSpecPos2]
                    intfStatus = "up" 
                    intfAccess = "" 
                    sshCmd="sh int " + intfName + " | i duplex"
                    intfDuplex = connection.send_command(sshCmd)
                    if "Auto-Duplex(Full-duplex), Auto-Speed(1000 Mbps)" in intfDuplex:
                        intfSpeed = "1Gb"
                        intfDuplex= "full"
                    elif  "Auto-Duplex(Full-duplex), Auto-Speed(10000 Mbps)" in intfDuplex:
                        intfSpeed = "10Gb"
                        intfDuplex= "full"
                    elif  "Full-duplex, 10000 Mbps" in intfDuplex:
                        intfSpeed = "10Gb"
                        intfDuplex= "full"
                    elif  "Full-duplex, 1000 Mbps" in intfDuplex:
                        intfSpeed = "1Gb"
                        intfDuplex= "full"
                    else:
                        intfSpeed = "N/A"
                        intfDuplex= "N/A"
                    intfSFP    = "N/A" 

                    printDebug("NO", "entry {} Descr {}  status {} sfp {} {} {}"   .format(intfName, intfDescription, intfStatus, intfSFP, intfSpeed, intfDuplex))



                    intfCat={}

                    intfCat = { 'device': switchName, 'port': intfName, 'switchOS': switchOS, 'switchLocation': switchLocation, \
                            'switchLocationNew': switchLocationNew, 'deviceConnected': intfDescription, 'deviceSwitchport': intfAccess, 'type': \
                            intfSFP, 'speed': intfSpeed, 'duplex': intfDuplex }
                    #print(" ==> device not found {} Adding {}" .format(deviceName, deviceCat))

                    interfaceList.append(intfCat)
                else:
                    printDebug("NO", "ignoring Interface {}" .format(intfEntries[0]))

        connection.disconnect()
        return interfaceList

    except RuntimeError as e1:
        #print("device: {}  not reachable" .format(switchName))
        #print("----------------------------------" .format(switchName))
        #print("Problem mit SSH Verbindung : {}" .format(e1))
        return interfaceList
    except gaierror as e2:
        #print("device: {}  not reachable" .format(switchName))
        #print("----------------------------------" .format(switchName))
        #print("Problem mit SSH Verbindung : {}" .format(e2))
        return interfaceList
    except TimeoutError as e2:
        #print("device: {}  not reachable" .format(switchName))
        #print("----------------------------------" .format(switchName))
        #print("Problem mit SSH Verbindung : {}" .format(e2))
        return interfaceList

def getInterfaceSwtich(credentials,  interfaceList, switchName, switchOS, switchLocation, switchLocationNew):
    try:
        #connection = device_connection_handler.connect(switchName, "cisco_ios", credentials)
        switchNameRaw=switchName
        if switchOS == "fex":
            posFex= switchName.find("-fex")
            switchNameRaw=switchName[0:posFex]
            fexNr=switchName[posFex+4:posFex+7]
            printDebug("NO", "SwtichnameRaw: "+switchNameRaw+"  fex: "+fexNr) 
            sshCmd="sh int status | i connected | i Eth"+fexNr
        elif switchOS == "nxos":
            printDebug("NO", "SwtichnameRaw: "+switchNameRaw) 
            sshCmd="sh int status | i connected | i Eth[1-9]/|mgmt"
        elif switchOS == "ios":
            sshCmd="sh int status | i connected"
        elif switchOS == "iosxe":
            sshCmd="sh int status | i connected"
        elif switchOS == "iosxe-asr":
            sshCmd="sh ip int brief | i up"

        connection = device_connection_handler.connect(switchNameRaw, "cisco_ios", credentials)
        #print("CMD : {}" .format(sshCmd))
        intfList = connection.send_command(sshCmd)
        #print("interfaceList {} type of {} " .format(intfList, type(intfList)))
        if (len(intfList) > -1):
            buf = intfList.split("\n")
            #print("buf {}" .format(buf))
            if switchOS != "iosxe-asr":
                for entry in buf:
                    intfEntries = re.split('\s+', entry)
                    if len(intfEntries) > 6 and intfEntries[0].find("Po") == -1:
                        #print("Entry {}, Entries{}" .format(entry, intfEntries))
                        lenEntries = len(intfEntries)
                        intfName = intfEntries[0]
                        intfDescription = intfEntries[1]
                        if intfEntries[1] == "connected":
                            nDelta = -1
                        elif intfEntries[2] == "connected":
                            nDelta = 0
                        elif intfEntries[3] == "connected":
                            intfDescription = intfEntries[1]+" "+intfEntries[2]
                            nDelta = 1
                        elif intfEntries[4] == "connected":
                            intfDescription = intfEntries[1]+" "+intfEntries[2]+" "+intfEntries[3]
                            nDelta = 2
                        elif intfEntries[5] == "connected":
                            intfDescription = intfEntries[1]+" "+intfEntries[2]+" "+intfEntries[3]+" "+intfEntries[4]
                            nDelta = 3
                        elif intfEntries[6] == "connected":
                            intfDescription = intfEntries[1]+" "+intfEntries[2]+" "+intfEntries[3]+" "+intfEntries[4]+" "+intfEntries[5]
                            nDelta = 4
                        elif intfEntries[7] == "connected":
                            intfDescription = intfEntries[1]+" "+intfEntries[2]+" "+intfEntries[3]+" "+intfEntries[4]+" "+intfEntries[5]+" "+intfEntries[6]
                            nDelta = 5
                        elif intfEntries[8] == "connected":
                            intfDescription = intfEntries[1]+" "+intfEntries[2]+" "+intfEntries[3]+" "+intfEntries[4]+" "+intfEntries[5]+" "+ \
                            intfEntries[6]+" "+intfEntries[7]
                            nDelta = 6


                        intfStatus = intfEntries[2+nDelta]
                        intfAccess = intfEntries[3+nDelta]
                        intfDuplex = intfEntries[4+nDelta]
                        intfSpeed  = intfEntries[5+nDelta]
                        intfSFP    = setIntfSFP(connection, intfName, switchOS, intfEntries[6+nDelta])

                        printDebug("YES", "entry {} Descr {}  status {} sfp {} len {} {} {}"   .format(intfName, intfDescription, intfStatus, intfSFP, lenEntries, intfSpeed, intfDuplex))

                        intfCat={}

                        intfCat = { 'device': switchName, 'port': intfName, 'switchOS': switchOS, 'switchLocation': switchLocation, \
                                'switchLocationNew': switchLocationNew, 'deviceConnected': intfDescription, 'deviceSwitchport': intfAccess, 'type': \
                                intfSFP, 'speed': intfSpeed, 'duplex': intfDuplex }
                        #print(" ==> device not found {} Adding {}" .format(deviceName, deviceCat))

                        interfaceList.append(intfCat)
                    elif len(intfEntries) == 6 and intfEntries[0].find("Po") == -1:
                        #-- no Descritpion
                        #print("Entry {}, Entries{}" .format(entry, intfEntries))
                        lenEntries = len(intfEntries)
                        intfName = intfEntries[0]
                        intfDescription = "NO DESCRIPTION" 
                        intfStatus = intfEntries[1]
                        intfAccess = intfEntries[2]
                        intfDuplex = intfEntries[3]
                        intfSpeed  = intfEntries[4]
                        intfSFP    = setIntfSFP(connection, intfName, switchOS, intfEntries[5])

                        printDebug("NO", "entry {} Descr {}  status {} sfp {} len {} {} {}"   .format(intfName, intfDescription, intfStatus, intfSFP, lenEntries, intfSpeed, intfDuplex))

                        intfCat={}

                        intfCat = { 'device': switchName, 'port': intfName, 'switchOS': switchOS, 'switchLocation': switchLocation, \
                                'switchLocationNew': switchLocationNew, 'deviceConnected': intfDescription, 'deviceSwitchport': intfAccess, 'type': \
                                intfSFP, 'speed': intfSpeed, 'duplex': intfDuplex }
                        #print(" ==> device not found {} Adding {}" .format(deviceName, deviceCat))

                        interfaceList.append(intfCat)
            elif switchOS == "iosxe-asr":
                for entry in buf:
                    intfEntries = re.split('\s+', entry)
                    if len(intfEntries) > 5 and (intfEntries[0].find("Ethernet") > -1 or re.search("0/0/[0-9]$", intfEntries[0]) is not None):
                        #print("Entry {}, Entries{}" .format(entry, intfEntries))
                        intfName = intfEntries[0]
                        intfDescription = "ASR Interface to find out" 
                        intfStatus = "connected"
                        intfAccess = "ASR Routed port"
                        intfDuplex = "ASR Routed Port N/A" 
                        intfSpeed  = "ASR Routed Port N/A"
                        intfSFP    = "ASR Routed Port N/A" 
                        sshCmd="sh int {} | i (Description|media type) " .format(intfName)
                        
                        

                        print("CMD ASR : {} auf {}" .format(sshCmd, switchName ))
                        intfList = connection.send_command(sshCmd)
                        #print("interfaceList {} type of {} " .format(intfList, type(intfList)))
                        if (len(intfList) > -1):
                            buf = intfList.split("\n")
                            print("buf {}" .format(buf))
                            for entry in buf:
                                intfEntries = entry.strip()
                                intfEntries = re.split('\s+', intfEntries)
                                print("Entry {}, Entries{}" .format(entry, intfEntries))
                                lenEntries = len(intfEntries)
                                if len(intfEntries) > 1:
                                    if intfEntries[0].startswith("Description"):
                                        intfDescription = intfEntries[1]
                                    else:
                                        intfDuplex = intfEntries[0] 
                                        intfSpeed  = intfEntries[2]
                                        intfSFP    = intfEntries[lenEntries-1] 


                        #print("entry {} {} {} {}"   .format(intfName, intfDescription, intfStatus, intfSFP, intfSpeed, intfDuplex))

                        intfCat={}

                        intfCat = { 'device': switchName, 'port': intfName, 'switchOS': switchOS, 'switchLocation': switchLocation, \
                                'switchLocationNew': switchLocationNew, \
                                'deviceConnected': intfDescription, 'deviceSwitchport': intfAccess, 'type': \
                                intfSFP, 'speed': intfSpeed, 'duplex': intfDuplex }
                        #print(" ==> device not found {} Adding {}" .format(deviceName, deviceCat))

                        interfaceList.append(intfCat)

        #---- for iosxe => catalyst 4500 get managment Interface
        if switchOS == "iosxe":
            sshCmd="sh ip int brief | i FastEthernet|GigabitEthernet0"
            intfList = connection.send_command(sshCmd)
            if (len(intfList) > -1):
                buf = intfList.split("\n")
                for entry in buf:
                    intfEntries = re.split('\s+', entry)
                    if len(intfEntries) > 6 and intfEntries[0].find("Po") == -1:
                        #print("Entry {}, Entries{}" .format(entry, intfEntries))
                        intfName = intfEntries[0]
                        intfDescription = "IOSXE mgmt Interface to find out" 
                        intfStatus = "connected"
                        intfAccess = "IOSXE mgmt port"
                        intfDuplex = "IOSXE mgmt Port N/A" 
                        intfSpeed  = "IOSXE mgmt Port N/A"
                        intfSFP    = "IOSXE mgmt Port N/A" 

                        #print("entry {} {} {} {}"   .format(intfName, intfDescription, intfStatus, intfSFP, intfSpeed, intfDuplex))

                        intfCat={}

                        intfCat = { 'device': switchName, 'port': intfName, 'switchOS': switchOS, 'switchLocation': switchLocation, \
                                'switchLocationNew': switchLocationNew, 'deviceConnected': intfDescription, 'deviceSwitchport': intfAccess, 'type': \
                                intfSFP, 'speed': intfSpeed, 'duplex': intfDuplex }
                        #print(" ==> device not found {} Adding {}" .format(deviceName, deviceCat))

                        interfaceList.append(intfCat)

        connection.disconnect()
        return interfaceList

    except RuntimeError as e1:
        #print("device: {}  not reachable" .format(switchName))
        #print("----------------------------------" .format(switchName))
        #print("Problem mit SSH Verbindung : {}" .format(e1))
        return interfaceList
    except gaierror as e2:
        #print("device: {}  not reachable" .format(switchName))
        #print("----------------------------------" .format(switchName))
        #print("Problem mit SSH Verbindung : {}" .format(e2))
        return interfaceList
    except TimeoutError as e2:
        #print("device: {}  not reachable" .format(switchName))
        #print("----------------------------------" .format(switchName))
        #print("Problem mit SSH Verbindung : {}" .format(e2))
        return interfaceList

def get_devices_name(device):
    try: 
       #print  ("IN LIBRENMS: hostname {}" .format(device))
       # collect devices from LibreNMS
       libre_api = librenms_api.LibreNMS(LIBRENMS_SERVER)
       apicall="/api/v0/devices/"+device.strip()
       #print("APICALL {}" .format(apicall))
       response = libre_api.api_call(apicall)
       #print("repseonse {}".format(response))
       #print  ("hostname {}" .format(device))
       device1=response["devices"]
       #print("repseonse 2 {}".format(device1))
       return response["devices"]
    except:
       return "Device not in LIBRENMS"

def getTotalInfSwitch(filenameYaml, switchName):

    yamlFile = read_yaml(filenameYaml)
    yamlFile = yamlFile + read_yaml("static_cwe_wet_inventory.yaml")
    printDebug("NO", yamlFile)

    interfaceList =[]
    #---- run over all switch in Yaml File
    for yamlEntry in yamlFile:
        switchNameYaml = yamlEntry.get("device")
        printDebug("NO", "compare {} with {} " .format(switchNameYaml, switchName))
        if switchNameYaml.find(switchName) > -1:
           printDebug("NO", "FOUND IT ")
           return yamlEntry.get("totalInterface")

    return 9999

def read_yaml(filename):
    """ A function to read YAML file"""
    with open(filename) as f:
        config = yaml.safe_load(f)
 
    return config

def addSwitchIntf(intfList, switch, port, deviceConnected):
    found = False
    intfCat={}

    intfCat = { 'device': switch, 'port': port, 'deviceConnected': deviceConnected }
    #print(" ==> device not found {} Adding {}" .format(deviceName, deviceCat))

    intfList.append(intfCat)
    return intfList

def searchIntfNetzDB(netzDB, switchNameRaw, intfName):
    
    interfaceList=[]
    #--- clean Interface 
    intfNameRaw=intfName
    x1=re.search("GigabitEthernet0$", intfNameRaw)

    if intfName.find("FastEthernet1") == -1 and intfName.find("Mgmt0") == -1 and intfName.find("mgmt0") == -1 and intfName.find("Management") ==\
    -1 and x1 is None:
        intfNameRaw=re.findall("[0-9/]", intfName)
        intfNameRawStr="".join(str(x) for x in intfNameRaw)
        intfNameRaw=intfNameRawStr
        printDebug("NO", "keine ManagementInterface gi0 oder Fa1 "+intfName+" "+intfNameRaw)

    #--- check if deviceName is fex, if yes then clean it
    switchName=switchNameRaw
    if switchName.find("-fex") > -1:
        switchNameRaw=switchName[0:switchName.find(":")]
        printDebug("NO", "looking in NetzDB for {} FOUND FEX {}" .format(switchNameRaw, switchName))

    printDebug("NO", "looking in NetzDB for {} {}" .format(switchNameRaw, intfNameRaw))

    with open(netzDB, mode = "r") as f:
        csvFile = csv.DictReader(f, delimiter=";")

        for line in csvFile:
            device1Intf=line["Port1"]
            device2Intf=line["Port2"]
            device1Name=line["Komponente1"]
            device2Name=line["Komponente2"]

            x=re.search(intfNameRaw+"$", device1Intf)
            y=re.search(intfNameRaw+"$", device2Intf)
            if x is None:
                printDebug("NO", " search "+device1Intf+" "+intfNameRaw+"$ RESULT is NONE type of x is NONE ")
            else:
                printDebug("NO", " search "+device1Intf+" "+intfNameRaw+"$ RESULT is FOUND")
            if y is None:
                printDebug("NO", " search "+device2Intf+" "+intfNameRaw+"$ RESULT is NONE type of y is NONE ")
            else:
                printDebug("NO", " search "+device2Intf+" "+intfNameRaw+"$ RESULT is FOUND")
            
            if (re.search(intfNameRaw+"$", device1Intf) is not None and device1Name ==switchNameRaw):
               printDebug("NO", "FOUND Entry in NetzDB for  {}:{} {}:{} " .format(device1Name, device1Intf, device2Name, device2Intf))
               # print(" COMPARE {}:{}:{} " .format(switchNameRaw, len (switchNameRaw), id(switchNameRaw)))
               connectedCat = { 'deviceConnectedNetzDB' : device2Name, 'deviceConnectedPortNetzDB': device2Intf }
               interfaceList.append(connectedCat)
               printDebug("NO", "ADDING 3 switch {} and interface {} in list {} {}" .format(switchNameRaw, intfName, intfNameRaw+"$", device1Intf))
            elif (re.search(intfNameRaw+"$", device2Intf) is not None   and device2Name ==switchNameRaw):
               printDebug("NO", "FOUND Entry in NetzDB for  {}:{} {}:{} " .format(device1Name, device1Intf, device2Name, device2Intf))
               # print(" COMPARE {}:{}:{} " .format(switchNameRaw, len (switchNameRaw), id(switchNameRaw)))
               connectedCat = { 'deviceConnectedNetzDB' : device1Name, 'deviceConnectedPortNetzDB': device1Intf }
               interfaceList.append(connectedCat)
               printDebug("NO", "ADDING 4 switch {} and interface {} in list" .format(switchNameRaw, intfName))
            elif (x1 is not None and device2Intf.find("gmt") > -1   and device2Name ==switchNameRaw):
               printDebug("NO", "FOUND Entry in NetzDB for  {}:{} {}:{} " .format(device1Name, device1Intf, device2Name, device2Intf))
               # print(" COMPARE {}:{}:{} " .format(switchNameRaw, len (switchNameRaw), id(switchNameRaw)))
               connectedCat = { 'deviceConnectedNetzDB' : device1Name, 'deviceConnectedPortNetzDB': device1Intf }
               interfaceList.append(connectedCat)
               printDebug("NO", "ADDING 2 switch {} and interface {} in list" .format(switchNameRaw, intfName))
            elif (x1 is not None and device1Intf.find("gmt") > -1   and device1Name ==switchNameRaw):
               printDebug("NO", "FOUND Entry in NetzDB for  {}:{} {}:{} " .format(device1Name, device1Intf, device2Name, device2Intf))
               # print(" COMPARE {}:{}:{} " .format(switchNameRaw, len (switchNameRaw), id(switchNameRaw)))
               connectedCat = { 'deviceConnectedNetzDB' : device2Name, 'deviceConnectedPortNetzDB': device2Intf }
               interfaceList.append(connectedCat)
               printDebug("NO", "ADDING 1 switch {} and interface {} in list" .format(switchNameRaw, intfName))
            elif (device1Intf.find("gmt") > -1   and device1Name ==switchNameRaw and intfNameRaw.find("Management") > -1 ):
               printDebug("NO", "FOUND Entry in NetzDB for  {}:{} {}:{} " .format(device1Name, device1Intf, device2Name, device2Intf))
               # print(" COMPARE {}:{}:{} " .format(switchNameRaw, len (switchNameRaw), id(switchNameRaw)))
               connectedCat = { 'deviceConnectedNetzDB' : device2Name, 'deviceConnectedPortNetzDB': device2Intf }
               interfaceList.append(connectedCat)
               printDebug("NO", "ADDING 1 switch {} and interface {} in list" .format(switchNameRaw, intfName))
            elif (device2Intf.find("gmt") > -1   and device2Name ==switchNameRaw and intfNameRaw.find("Management") > -1):
               printDebug("NO", "FOUND Entry in NetzDB for  {}:{} {}:{} " .format(device1Name, device1Intf, device2Name, device2Intf))
               # print(" COMPARE {}:{}:{} " .format(switchNameRaw, len (switchNameRaw), id(switchNameRaw)))
               connectedCat = { 'deviceConnectedNetzDB' : device1Name, 'deviceConnectedPortNetzDB': device1Intf }
               interfaceList.append(connectedCat)
               printDebug("NO", "ADDING 1 switch {} and interface {} in list" .format(switchNameRaw, intfName))
            elif  (device2Name ==switchNameRaw or device1Name ==switchNameRaw):
               printDebug("NO",  " NOT FOUND interface {}  NetzDB-INTF {} netzdb-inf2 {}"  .format(intfNameRaw, device1Intf, device2Intf))
               


    return interfaceList

def searchNetzDB(netzDB, interfaceList, switchNameRaw):

    with open(netzDB, mode = "r") as f:
        csvFile = csv.DictReader(f, delimiter=";")

        for line in csvFile:
            device1Intf=line["Port1"]
            device2Intf=line["Port2"]
            device1Name=line["Komponente1"]
            device2Name=line["Komponente2"]

            #print("from NetzDB {}/{} {}/{} " .format(device1Name, device1Intf, device2Name, device2Intf, ))
            #if (device1Name.find(switchNameRaw) == -1 and device2Name.find(switchNameRaw)):
            if (device1Name != switchNameRaw  and device2Name != switchNameRaw):
                #print("SKIPPING {}:{}:{} {}:{} " .format(device1Name, len(device1Name), id(device1Name), device2Name, len(device2Name)))
               # print(" COMPARE {}:{}:{} " .format(switchNameRaw, len (switchNameRaw), id(switchNameRaw)))

                z=0
            else:
                #if (device1Name.find(switchNameRaw) > -1):
                if (device1Name == switchNameRaw):
                    switchIntf=line["Port1"]
                    switchIntfConnected=device2Name+":"+line["Port2"]
                elif (device2Name == switchNameRaw):
                    switchIntf=line["Port2"]
                    switchIntfConnected=device1Name+":"+line["Port1"]

                interfaceList=addSwitchIntf(interfaceList, switchNameRaw, switchIntf, switchIntfConnected)
                printDebug("NO", "ADDING switch {} and interface {} in list" .format(switchNameRaw, switchIntf))
    return interfaceList

def printDebug(debugMode, stringToPrint):
    debugMode=debugMode.upper()
    if debugMode=="YES":
         print("DEBUG {}" .format(stringToPrint))

def printStaticEntry(switchNameSave, i, j, nPortTotal, interfaceStaticList):


    #-- get Static interface as well
    sToPrint="{}" .format(interfaceStaticList)
    printDebug("NO", sToPrint)
    
    z=0
    for entry in interfaceStaticList:
        switchName = entry["device"]
        switchPort = entry["port"]
        deviceConnected = entry["deviceConnected"]
        deviceSwitchport = entry["deviceSwitchport"]
        deviceLocation = entry["switchLocation"]
        deviceLocationNew = entry["switchLocationNew"]
        deviceConnectedNetzDB = entry["deviceConnected"]
        deviceConnectedPortNetzDB = entry["deviceSwitchport"]
        deviceSFP = entry["type"]
        deviceSpeed = entry["speed"]
        printDebug("NO","switchName To Find {} switchName aus static {}" .format(switchNameSave, switchName))
        if (switchNameSave == switchName):
            j=j+1
            nPortTotal=nPortTotal+1
            if (z==0):
                print("{:3}: WARNING:                    special Ports (Connected but down):" .format(i))
                z=1
            print("{:3}: device {:20} interface: {:3}:{:10}  Connected: {:20} {:6} {:15} \tInfo from NetzDB {}  {} location WE: {} location ZO: {} " .format(i, switchName, \
                    j,switchPort, deviceConnected, deviceSpeed, deviceSFP, \
                    deviceConnectedNetzDB, deviceConnectedPortNetzDB, deviceLocation, deviceLocationNew))

        #intfCat = { 'device': switchName, 'port': switchPort, 'switchOS': switchOS, 'switchLocation': switchLocation, \
        #            'switchLocationNew': switchLocationNew, 'deviceConnected': switchConnectedNetzDB, 'deviceSwitchport': \
        #             switchConnectedPortNetzDB, 'type': \
        #             intfSFP, 'speed': intfSpeed, 'duplex': intfDuplex }
        
    return j

def main():
    delimiter = "###########################################################################\n"
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--file', help="Name des NetzDB export als csv", required=False, default="cwe_wet_inventory.csv");
    parser.add_argument('--switchYAML', help="Name des switch YAML File. Das ist die Quelle des Skripts und wird nicht verändert", required=False, default="cwe_wet_inventory.yaml");
    parser.add_argument('--interfaceYAML', help="Name des Interface YAML File. Das File wird von diesem Skript neu geschrieben (also überschreibt das  \
            alte YAML File)", required=False, default="cwe_wet_interface.yaml");
    parser.add_argument('--debug', help="YES: Print Debug Message NO: no Debug Messages displayed     DEFAULT=no",  required=False, default="no");
    #parser.add_argument('--sleep', required=False, default=2);
    parser.add_argument('--switch', help="mit diesem Parameter kann etweder 'all' oder einen switchname eingegeben werden      DEFAULT: all", required=False, default="all");
    parser.add_argument('--site', help="mit diesem Parameter kann etweder 'all' oder einen switchname eingegeben werden      DEFAULT: all", \
            required=False, default="WE");
    parser.add_argument('--mode', help="mit diesem Parameter kann auf OS eingegrenzt werden. Mögliche OS sind ios, iosxe, iosxe-asr, nxos, asa, fex, \
    ping, generic, fabos, netscaler, all       DEFAULT: all", required=False, default="all");
    parser.add_argument('--generateVerkablungsrequest', help="generiert den Verkabelungsrequest falls gesetzt", \
            required=False, action='store_true');
    args = parser.parse_args()

    filename=args.file
    filenameYaml=args.switchYAML
    interfaceYaml=args.interfaceYAML
    site=args.site
    if site.startswith("BE"):
        filenameYaml="cwe_bern_inventory.yaml"
        interfaceYaml="cwe_bern_inventory.yaml"


    debugMode=args.debug
    switchToFind=args.switch
    deviceModeToFind=args.mode
    generateVR=args.generateVerkablungsrequest
    interfaceYaml=deviceModeToFind+"_"+interfaceYaml
    #mode=args.mode
    #if (mode != "LONG") and (mode != "SHORT"):
    #    raise Exception("start programm with --mode SHORT|LONG (Default=SHORT)")
    #sleeptime=int(args.sleep)

    print(delimiter)
    print()
    print("starting cwe_check_ssh.py")
    print()
    print("INPUT:            {:30} NetzDB csv" .format(filename))
    print("                  {:30} Switchinvenory " .format(filenameYaml))
    print("                  generateVerkabelungsrequest:   {}    " .format(generateVR))
    print("OUTPUT:           {:30} Interface Inventory wird geschrieben " .format(interfaceYaml))
    print()
    print("PARAMETER: ")
    print("  --filem         {:30} NetzDB csv" .format(filename))
    print("  --switchYAML    {:30} Switchinvenory " .format(filenameYaml))
    print("  --InterfaceYAML {:30} Interface Inventory wird geschrieben " .format(interfaceYaml))
    #print("  --mode {} " .format(mode))
    #print("  --sleep {} " .format(sleeptime))
    print("  --switch        {:30} Switch search parameter" .format(switchToFind))
    print("  --debug         {:30} debugMode " .format(debugMode))
    print("  --site          {:30} debugMode " .format(site))
    print("  --generateVerkabelungsrequest                  {} (0=False 1=True) " .format(generateVR))
    print()
    print(delimiter)


    #-- Anmelde Login für Netzwerkgeräte
    if "USER1_NAME" not in os.environ:
        raise Exception("Environment Variable USER1_NAME must be set")
    if "USER1_PASS" not in os.environ:
        raise Exception("Environment Variable USER1_PASS must be set")
    credentials = [
        {
            "username": os.environ["USER1_NAME"],
            "password": os.environ["USER1_PASS"]
        }
    ]

    #---- get All Interface which must be moved but are down (special connections => Mainframe)
    interfaceStaticList=[]
    yamlFile= read_yaml("static_cwe_wet_interface.yaml")
    if site.startswith("BE"):
        yamlFile= read_yaml("static_cwe_bern_interface.yaml")
    printDebug("NO", yamlFile)

    nActivity=0
    if  yamlFile is not None:
        for yamlEntry in yamlFile:
            if (nActivity % 4 == 0):
               print(".", end = '', flush=True)
            nActivity=nActivity+1

            switchName = yamlEntry.get("device")
            switchNameRaw = switchName
            pos=switchName.find(".")
            if (pos > -1):
                switchNameRaw = switchName[0:pos]
            #if (switchToFind != "all" and switchNameRaw.find(switchToFind) == -1):
            #     continue

            switchPort                = yamlEntry.get("port")
            switchOS                  = yamlEntry.get("switchOS")
            switchLocation            = yamlEntry.get("switchLocation")
            switchLocationNew         = yamlEntry.get("switchLocationNew")
            switchConnectedNetzDB     = yamlEntry.get("deviceConnectedNetzDB")
            switchConnectedPortNetzDB = yamlEntry.get("deviceConnectedPortNetzDB")
            switchConnectedPortNetzDB = yamlEntry.get("deviceConnectedPortNetzDB")
            intfStatus = "connected"
            intfAccess = yamlEntry.get("deviceSwitchPort")
            intfDuplex = yamlEntry.get("duplex") 
            intfSpeed  = yamlEntry.get("speed") 
            intfSFP    = yamlEntry.get("type") 

            #---- OS = ping => ignore yet
            if deviceModeToFind != "all" and deviceModeToFind != switchOS:
                continue

            #---- looking for interface for device

            printDebug("NO", "entry {} Descr {}  status {} sfp {} {} {}"   .format(switchPort, switchConnectedPortNetzDB, "not Connected", intfSFP, intfSpeed, intfDuplex))

            intfCat={}

            intfCat = { 'device': switchName, 'port': switchPort, 'switchOS': switchOS, 'switchLocation': switchLocation, \
                    'switchLocationNew': switchLocationNew, 'deviceConnected': switchConnectedNetzDB, 'deviceSwitchport': \
                     switchConnectedPortNetzDB, 'type': \
                     intfSFP, 'speed': intfSpeed, 'duplex': intfDuplex }
            #print(" ==> device not found {} Adding {}" .format(deviceName, deviceCat))

            interfaceStaticList.append(intfCat)
            #---- find interface in NetzDB for device
            printDebug("NO", "looking for Entry for switchNameRaw in Netzdb")
    
    print(interfaceStaticList)

    #---- read switch Yaml File
    yamlFile = read_yaml(filenameYaml)
    printDebug("NO", yamlFile)
    if site.startswith("BE"):
        yamlFile = yamlFile + read_yaml("static_cwe_bern_inventory.yaml")
    else:    
        yamlFile = yamlFile + read_yaml("static_cwe_wet_inventory.yaml")
    printDebug("NO", yamlFile)
    i=0
    j=0



    interfaceList =[]
    #---- run over all switch in Yaml File
    for yamlEntry in yamlFile:
        if (nActivity % 4 == 0):
           print(".", end = '', flush=True)
        nActivity=nActivity+1

        j=j+1
        switchName = yamlEntry.get("device")
        switchNameRaw = switchName
        pos=switchName.find(".")
        if (pos > -1):
            switchNameRaw = switchName[0:pos]
        if (switchToFind != "all" and switchNameRaw.find(switchToFind) == -1):
            continue

        switchOS   = yamlEntry.get("os")
        switchLocation = yamlEntry.get("location")
        switchLocationNew = yamlEntry.get("locationNew")
        switchInterfaceTotal = yamlEntry.get("totalInterface")
        #print(" found a device {} {}" .format(switchNameRaw, switchOS))

        #---- OS = ping => ignore yet
        if deviceModeToFind != "all" and deviceModeToFind != switchOS:
            print(" found a device {} {} but not relevant" .format(switchNameRaw, switchOS))
            continue
        if switchOS == "ping":
            continue
        elif switchOS == "fabos":
            continue
        elif switchOS == "generic":
            continue
        #elif switchOS == "asa":
        #    continue
        else:
            i=i+1
        print(" found a device {} {}" .format(switchNameRaw, switchOS))
        #---- looking for interface for device
        printDebug("YES", "looking for active Interface on Switch switchNameRaw "+switchNameRaw)
        if switchOS == "asa":
            interfaceList=getInterfaceASA(credentials,  interfaceList, switchNameRaw, switchOS, switchLocation, switchLocationNew)
        else:
            #print("OK now lloking at {}" .format(switchNameRaw))
            interfaceList=getInterfaceSwtich(credentials,  interfaceList, switchNameRaw, switchOS, switchLocation, switchLocationNew)
        
        #---- find interface in NetzDB for device
        printDebug("NO", "looking for Entry for switchNameRaw in Netzdb")
    
    #---- find interface in NetzDB for device
    i=j=0
    nPortTotal=0
    nSwitchTotal=0
    switchNameSave=""
    
    for entry in interfaceList:
        if (nActivity % 4 == 0):
           print(".", end = '', flush=True)
        nActivity=nActivity+1
        switchName = entry["device"]
        switchPort = entry["port"]
        switchConnected = entry["deviceConnected"]
        if (switchNameSave == switchName):
            j=j+1
            nPortTotal=nPortTotal+1
        else:
            print("")

            i=i+1
            nSwitchTotal=nSwitchTotal+1
            nPortTotal=nPortTotal+1
            j=1
            switchNameSave = switchName
        intfList=searchIntfNetzDB(filename, switchName, switchPort)
        if len(intfList) == 0:
            printDebug(debugMode, "{:3}: device {:20} interface: {:3}:{:20}  deviceConnected: {:20} \tNO INFO in NetzDB" .format(i, switchName, j,switchPort, switchConnected))
            connectedCat = { 'deviceConnectedNetzDB' : "NOT FOUND in NetzDB", 'deviceConnectedPortNetzDB': "NOT FOUND in NetzDB" }
            intfList.append(connectedCat)
        else:
            for entry1 in intfList:
                deviceConnected=entry1["deviceConnectedNetzDB"]
                deviceConnectedPort=entry1["deviceConnectedPortNetzDB"]
                printDebug(debugMode, "{:3}: device {:20} interface: {:3}:{:20}  deviceConnected: {:20} \tInfo from NetzDB {}  {} " .format(i, switchName, j,switchPort, switchConnected, \
                    deviceConnected, deviceConnectedPort))
        sToPrint="DEBUG entry vor Update {}" .format(entry)
        printDebug("NO", sToPrint)
        entry.update(intfList[0])
        sToPrint="DEBUG entry nach Update {}" .format(entry)
        printDebug("NO", sToPrint)

    #---- print the complete Dict if needed
    sToPrint="{}" .format(interfaceList)
    printDebug(debugMode, sToPrint)
    
    i=j=0
    nPortTotal=0
    nSwitchTotal=0
    switchNameSave=""
    if len(interfaceList) > 0:
        for entry in interfaceList:
            switchName = entry["device"]
            switchPort = entry["port"]
            deviceConnected = entry["deviceConnected"]
            deviceSwitchport = entry["deviceSwitchport"]
            deviceLocation = entry["switchLocation"]
            deviceLocationNew = entry["switchLocationNew"]
            deviceConnectedNetzDB = entry["deviceConnectedNetzDB"]
            deviceConnectedPortNetzDB = entry["deviceConnectedPortNetzDB"]
            deviceSFP = entry["type"]
            deviceSpeed = entry["speed"]
            if (switchNameSave == switchName):
                j=j+1
                nPortTotal=nPortTotal+1
            else:

                if i > 0:
                    jVorStatic = j

                    j=printStaticEntry(switchNameSave, i, j, nPortTotal, interfaceStaticList)
                    staticPorts=j-jVorStatic
                    nPortTotal = nPortTotal + staticPorts
                    printDebug("NO", "looking for total number of interface for {}" .format(switchNameSave))
                    nInterfaceTotal=getTotalInfSwitch(filenameYaml, switchNameSave) 
                    print("     --------------------------------------------------------")
                    print("{:3}: device {:20} interface TOTAL: {}/{}" .format(i, switchNameSave, j, nInterfaceTotal))
                    print("")

                i=i+1
                nSwitchTotal=nSwitchTotal+1
                nPortTotal=nPortTotal+1
                j=1
                switchNameSave = switchName
            print("{:3}: device {:20} interface: {:3}:{:25}  Connected: {:20} {:6} {:15} \tInfo from NetzDB {}  {} location WE: {} location ZO: {} " .format(i, switchName, \
                    j,switchPort, deviceConnected, deviceSpeed, deviceSFP, \
                    deviceConnectedNetzDB, deviceConnectedPortNetzDB, deviceLocation, deviceLocationNew))
    else:
        printDebug("NO", "print static entries")

        jVorStatic = j
        i=i+1
        nSwitchTotal=nSwitchTotal+1
        switchNameSave=switchToFind
        j=printStaticEntry(switchToFind, i, j, nPortTotal, interfaceStaticList)
        staticPorts=j-jVorStatic

        nPortTotal = nPortTotal + staticPorts
        printDebug("NO", "looking for total number of interface for {}" .format(switchNameSave))
        nInterfaceTotal=getTotalInfSwitch(filenameYaml, switchNameSave) 
        print("     --------------------------------------------------------")
        nInterfaceTotal=getTotalInfSwitch(filenameYaml, switchNameSave) 
        print("{:3}: device {:20} interface TOTAL: {}/{}" .format(i, switchNameSave, j, nInterfaceTotal))
        print("")
        i=0

    #-- get Static interface as well
    sToPrint="{}" .format(interfaceStaticList)
    printDebug(debugMode, sToPrint)
    
    if i > 0:
        jVorStatic = j
        j=printStaticEntry(switchNameSave, i, j, nPortTotal, interfaceStaticList)

        staticPorts=j-jVorStatic
        nPortTotal = nPortTotal + staticPorts
        print("     --------------------------------------------------------")
        nInterfaceTotal=getTotalInfSwitch(filenameYaml, switchNameSave) 
        print("{:3}: device {:20} interface TOTAL: {}/{}" .format(i, switchNameSave, j, nInterfaceTotal))
        print("")

    #---- write neues interfaceYAML File
    print("")
    print("")
    print("writing YAML File {}" .format(interfaceYaml))
    with open(interfaceYaml, 'w') as outputFile:
        documents = yaml.dump(interfaceList, outputFile)

    print("")
    print("")
    print("")
    print("Summary ")
    print("----------------------------------------------")
    print("{} Switch von Total {} relevant" .format(i, nSwitchTotal))
    print("Total Verbindungen: {} " .format(nPortTotal))
    print("")
    print("")
    print("")


if __name__ == "__main__":
    main()

