from datetime import datetime
import os
import netmiko
import textfsm
import logging
import re
import io
import argparse
#import urllib3
#import librenms_api
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
LIBRENMS_SERVER = "librenms.mgmt.local"
DEVICEIP = "172.29.180.107"

traceroute = '''
r2#traceroute 90.0.0.9 source 33.0.0.2
traceroute 90.0.0.9 source 33.0.0.2
Type escape sequence to abort.
Tracing the route to 90.0.0.9
VRF info: (vrf in name/id, vrf out name/id)
  1 10.0.12.1 1 msec 0 msec 0 msec
  2 15.0.0.5  0 msec 5 msec 4 msec
  3 57.0.0.7  4 msec 1 msec 4 msec
  4 79.0.0.9  4 msec *  1 msec
'''


def main():
  with open('traceroute.template.cwe') as template:
    fsm = textfsm.TextFSM(template)
    result = fsm.ParseText(traceroute)

  print(fsm.header)
  print(result)

  for itemFSM in result:
      print("Hop: {}  IP: {}" .format(itemFSM[0], itemFSM[1]))


if __name__ == "__main__":
    main()

