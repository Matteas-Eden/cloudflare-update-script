#!/usr/bin/env python3
"""
The purpose of this script is regularly check the public IP of
the router this machine is connected to, then update the domain
record on Cloudflare's servers accordingly.

Usage: ./cloudflareUpdateScript.py [-sd]
Where:
    -s = silent
    -d = dry
"""

from dotenv import load_dotenv
from datetime import datetime
import CloudFlare
import os
import subprocess
import sys


def getDNSRecord(cf, zone_name, url):
    zones = cf.zones.get(params={"name": zone_name})
    zone_id = zones[0]["id"]

    dns_params = {"name": url, "match": "all"}
    dns_records = cf.zones.dns_records.get(zone_id, params=dns_params)

    if len(dns_records) != 1:
        log("Unexpected number of DNS records returned: " + len(dns_records),
            1)
        exit()

    dns_record = dns_records[0]

    return (dns_record, zone_id)


def getCurrentPublicIP():
    public_ip = (subprocess.check_output(["curl", "ifconfig.co",
                                          "-s"]).decode("utf-8").strip())
    return public_ip


def updateIPOnDNS(cf, zone_id, dns_record, new_ip):

    dns_record_id = dns_record['id']
    dns_record['content'] = new_ip
    try:
        dns_record = cf.zones.dns_records.put(zone_id,
                                              dns_record_id,
                                              data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        log(e)

    log("Updated DNS w/ IP: " + new_ip)


def log(msg, severity=0):
    """
    Simple logging function
    """
    if LOGGING:
        if severity == 0:
            prefix = "LOG"
        elif severity == 1:
            prefix = "ERR"
            logged = "[{0}] [{1}] {2}".format(datetime.now(), prefix, msg)
            print(logged)
            try:
                with open(LOGGING_FILE, "a") as f:
                    f.write(logged + "\n")
            except FileNotFoundError:
                with open(LOGGING_FILE, "w") as f:
                    f.write(logged + "\n")


def main():

    # Expose some globals to make calls to log() easier
    global LOGGING_FILE
    global LOGGING

    LOGGING = True

    if ("-s" or "--silent") in sys.argv:
        LOGGING = False

    load_dotenv()
    API_TOKEN = os.getenv("API_TOKEN")
    RECORD_NAME = os.getenv("RECORD_NAME")
    ZONE_NAME = os.getenv("ZONE_NAME")
    LOGGING_FILE = os.getenv("LOGGING_FILE")

    cf = CloudFlare.CloudFlare(token=API_TOKEN)

    dns_record, zone_id = getDNSRecord(cf, ZONE_NAME, RECORD_NAME)
    dns_record_ip = dns_record['content']
    public_ip = getCurrentPublicIP()

    if dns_record_ip != public_ip:
        updateIPOnDNS(cf, zone_id, dns_record, public_ip)
    else:
        log("No change in IP: " + dns_record_ip)


if __name__ == "__main__":
    main()
