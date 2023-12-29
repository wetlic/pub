from python_network_tools import device_connection_handler
#from paramiko.ssh_exception import  NetMikoTimeoutException
from paramiko.ssh_exception import SSHException
from socket import gethostbyname, gaierror
from time import sleep
from datetime import datetime
import os
import netmiko

import logging
import re
import io
import argparse
#import urllib3
#import librenms_api
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_devices_name(device):
    print  ("IN LIBRENMS: hostname {}" .format(device))
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


def main():
    delimiter = "###########################################################################\n"
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--file', required=False, default="ca_devices.txt");
    #parser.add_argument('--mode', required=False, default="SHORT");
    parser.add_argument('--sleep', required=False, default=2);
    args = parser.parse_args()

    filename=args.file
    #mode=args.mode
    #if (mode != "LONG") and (mode != "SHORT"):
    #    raise Exception("start programm with --mode SHORT|LONG (Default=SHORT)")
    sleeptime=int(args.sleep)

    print(delimiter)
    print()
    print("starting cwe_check_ssh.py")
    print()
    print("  --filem {} " .format(filename))
    #print("  --mode {} " .format(mode))
    print("  --sleep {} " .format(sleeptime))
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
    f = open(filename, "r")

    for line in f:
        device=line.strip("\n")
        try:
            #print("NOW device {}" .format(device))
            connection = device_connection_handler.connect(device, "cisco_ios", credentials)

            switchVersion = connection.send_command("show version ")
            #print (switchVersion)
            switchVersionSplit = switchVersion.split(",")
            switchVersionSplit = switchVersionSplit[1].split("\n")
            #print("len {}" .format(len(lineStrip)))
            print("{}: {} ssh ok " .format(device, switchVersionSplit[0]))
            connection.disconnect()
            sleep(sleeptime)


        #except Exception as err:
        #        exception_type = type(err).__name__
        #        print(exception_type)
        except RuntimeError as e1:
                print(delimiter)
                print("device: {}  not reachable" .format(device))
                print("----------------------------------" .format(device))
                print("Problem mit SSH Verbindung : {}" .format(e1))
        except gaierror as e2:
                print(delimiter)
                print("device: {}  not reachable" .format(device))
                print("----------------------------------" .format(device))
                print("Problem mit SSH Verbindung : {}" .format(e2))

if __name__ == "__main__":
    main()

