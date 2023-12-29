import logging

from netmiko import ConnectHandler
from paramiko import ssh_exception


def connect(device, device_type, credentials, secret=None):
    """
    connect to device (Netmiko abstraction)
    remember to always close connection, e.g.:
        try:
            connection = connect("been18-1u-321.mgmt.local", "cisco_ios", credentials)

            # use connection
        finally:
            # always close session
            connection.disconnect()

    :param device: hostname/fqdn
    :param credentials: list of credentials: [{"username": "", "password": ""}, ]
    :param device_type: Netmiko supported device type
    :param secret: optional enable password
    :rtype: open Netmiko connection object)
    """
    connection = None
    device_dict = {
        "device_type": device_type,
        "host": device,
    }
    # set enable secret if defined
    if secret is not None:
        device_dict["secret"] = secret

    for credential in credentials:
        # set credentials
        device_dict["username"] = credential["username"]
        device_dict["password"] = credential["password"]

        # connect
        try:
            logging.info(
                "try to connect to device " + device_dict["host"] +
                " with type " + device_dict["device_type"] +
                " and username " + device_dict["username"]
            )
            connection = ConnectHandler(**device_dict)

            # connection successfull -> break loop
            logging.debug("ssh connection to " + device + " successfull")
        except ssh_exception.NetMikoAuthenticationException:
            # login failed, try next credentials
            logging.info("login failed, try next credentials")
            continue
        except ssh_exception.SSHException:
            if device_dict["device_type"] == "cisco_ios":
                try:
                    device_dict["device_type"] = "cisco_ios_telnet"
                    connection = ConnectHandler(**device_dict)
                except ssh_exception.NetMikoAuthenticationException:
                    # login failed, try next credentials
                    logging.info("login failed, try next credentials")
            continue

    # check if login was successful
    if connection is None:
        # login failed, possibly wrong credentials
        raise RuntimeError("connection to device " + device + " failed")
    else:
        return connection
