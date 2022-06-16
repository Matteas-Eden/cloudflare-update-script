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

CRITICAL_MSG = "Critical error encountered. Terminating script..."


def getDNSRecord(cf, zone_name, url):
    log(f'Fetching zone ID from CloudFlare for {zone_name}...')
    zones = cf.zones.get(params={"name": zone_name})
    zone_id = zones[0]["id"]

    log(f'Fetching DNS records from CloudFlare for {url}...')
    dns_params = {"name": url, "match": "all"}
    dns_records = cf.zones.dns_records.get(zone_id, params=dns_params)

    if len(dns_records) != 1:
        log("Unexpected number of DNS records returned: " + len(dns_records),
            1)
        log(CRITICAL_MSG, 1)
        exit(1)

    dns_record = dns_records[0]

    return (dns_record, zone_id)


def getCurrentPublicIP():
    log("Querying public IP...")
    public_ip = (subprocess.check_output(["curl", "ifconfig.co",
                                          "-s"]).decode("utf-8").strip())
    if public_ip == '':
        log("Failed to obtain public IP", 1)
        log(CRITICAL_MSG, 1)
        exit(1)
    log(f"Obtained public IP: {public_ip}")
    return public_ip


def updateIPOnDNS(cf, zone_id, dns_record, new_ip):

    log("Updating DNS record...")
    dns_record_id = dns_record['id']
    dns_record['content'] = new_ip
    try:
        dns_record = cf.zones.dns_records.put(zone_id,
                                              dns_record_id,
                                              data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError:
        log('Could not update DNS record on CloudFlare', 1)
        log(CRITICAL_MSG, 1)
        exit(1)

    log("Updated DNS record w/ IP: " + new_ip)


def log(msg, severity=0):
    """
    Simple logging function

    Takes in a message, and prints to terminal. Also writes that
    message to a log file, if one was specified in .env.

    Optionally adds the prefix "ERR" if severity is > 0.
    """
    if LOGGING:
        if severity == 0:
            prefix = "LOG"
        elif severity >= 1:
            prefix = "ERR"
        logged = "[{0}] [{1}] {2}".format(datetime.now(), prefix, msg)
        print(logged)
        if LOGGING_FILE:
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

    if LOGGING_FILE and not (".log" in LOGGING_FILE):
        LOGGING_FILE += ".log"

    log('Starting script...')

    if LOGGING_FILE:
        log(f"Logs will be saved in {os.path.join(os.getcwd(), LOGGING_FILE)}")

    log(f"Updating record '{RECORD_NAME}' in zone '{ZONE_NAME}...'")
    cf = CloudFlare.CloudFlare(token=API_TOKEN)

    dns_record, zone_id = getDNSRecord(cf, ZONE_NAME, RECORD_NAME)
    dns_record_ip = dns_record['content']
    public_ip = getCurrentPublicIP()

    log(f"Current IP on DNS: {dns_record_ip}")

    if dns_record_ip != public_ip:
        updateIPOnDNS(cf, zone_id, dns_record, public_ip)
    else:
        log(f"No change in IP ({dns_record_ip} == {public_ip})")

    log('Exiting script...')


if __name__ == "__main__":
    main()
