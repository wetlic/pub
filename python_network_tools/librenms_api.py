import json
import os
import requests


class LibreNMSError(Exception):
    pass


class LibreNMSAddDevicePingError(LibreNMSError):
    pass


class LibreNMSAddDeviceSnmpError(LibreNMSError):
    pass


class LibreNMSAddDeviceDuplicateError(LibreNMSError):
    pass


class LibreNMS:
    # see https://docs.librenms.org/API/
    def __init__(self, hostname):
        """
        :param hostname: LibreNMS server
        """
        if "LIBRENMS_API_TOKEN" not in os.environ:
            raise Exception("Environment Variable LIBRENMS_API_TOKEN must be set")
        self.hostname = hostname
        self.headers = {
            "X-Auth-Token": os.environ["LIBRENMS_API_TOKEN"]
        }

    def __get(self, url):
        r = requests.get("https://" + self.hostname + url, headers=self.headers, verify=False)
        r.raise_for_status()
        response = json.loads(r.text)
        if "error" in response:
            raise Exception("api error: " + str(response))
        return response

    def __post(self, url, post_data):
        r = requests.post("https://" + self.hostname + url, headers=self.headers, json=post_data, verify=False)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            if r.status_code == 500:
                #applications specific error, handle in calling method
                return json.loads(r.text)
            raise
        return json.loads(r.text)

    def list_api_capabilities(self):
        """
        list possible API calls
        :return: response as dict
        """
        response = self.__get("/api/v0")
        print(response)

    def api_call(self, url):
        """
        call LibreNMS api
        :param url: URL, e.g. /api/v0/devices
        :return: response as dict
        """
        return self.__get(url)

    def add_device(self, hostname, snmp_version):
        if snmp_version not in ["v1", "v2c", "v3"]:
            raise Exception("unknown or unsupported snmp version")
        response = self.__post(
            "/api/v0/devices",
            {
                "hostname": hostname,
                "version": snmp_version,
            }
        )
        if response["status"] == "error":
            if response["message"].startswith("Could not ping"):
                raise LibreNMSAddDevicePingError(response["message"]) 
            if response["message"].endswith("please check the snmp details and snmp reachability"):
                raise LibreNMSAddDeviceSnmpError(response["message"])
            if  response["message"].startswith("Already have host"):
                raise LibreNMSAddDeviceDuplicateError(response["message"])
            raise LibreNMSError(response["message"])
        return response


# ---------- helper methods


def device_is_disabled(device):
    """
    check if device is disabled in LibreNMS
    :param device: response["devices"] from "/api/v0/devices"
    :return: True/False
    """
    if 1 == device["disabled"]:
        return True
    else:
        return False

