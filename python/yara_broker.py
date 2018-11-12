#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This tool extracts all yara rules and stores them into a folder, each file is named based on a checksum
__author__ = "Dennis Rand"
__copyright__ = "Copyright 2018, eCrimeLabs"
__license__ = "MIT"
__email__ = "contact@ecrimelabs.dk"
__status__ = "Production"

import yara
import hashlib
import string
import random
import requests
import json
import re
import argparse
import sys
import os
from keys import broker_url, broker_key


def json_validator(data):
    try:
        json.loads(data)
        return True
    except ValueError as error:
        return False

def check_directory_writable(directory):
    try:
        tmp_prefix = "write_tester";
        count = 0
        filename = os.path.join(directory, tmp_prefix)
        while(os.path.exists(filename)):
            filename = "{}.{}".format(os.path.join(directory, tmp_prefix),count)
            count = count + 1
        f = open(filename,"w")
        f.close()
        os.remove(filename)
        return True
    except Exception as e:
        #print "{}".format(e)
        return False

def fetch_broker_data(type, age):
    url = broker_url + "/apiv1/" + type + "/yara/" + age + "/" + broker_key + "/json"
    try:
        r = requests.get(url,timeout=360) #
        r.raise_for_status()
    except requests.exceptions.RequestException as err:
        print ("\r\nOOps: Something Else",err)
        sys.exit()
    except requests.exceptions.HTTPError as errh:
        print ("\r\nHttp Error:",errh)
        sys.exit()
    except requests.exceptions.ConnectionError as errc:
        print ("\r\nError Connecting:",errc)
        sys.exit()
    except requests.exceptions.Timeout as errt:
        print ("\r\nTimeout Error:",errt)
        sys.exit()

    if (r.status_code == requests.codes.ok):
        if(type == "feed"):
            outputs = "# Checksum of below data: " + r.headers.get('X-body-checksum') + "\r\n"
            outputs += r.text
        else:
            outputs = r.text

        return (outputs)
    else:
        print ("Error occoured when listing API content")
        sys.exit()

def parse_json_object(json_object, output, folder):
    # Data holders
    if not (check_directory_writable(folder)):
        print ("An error occoured in relation to writting to folder " + output)
        sys.exit(1)

    for rules in json_object:
        # Create Checksum
        yara_hash = (hashlib.md5(rules.encode('utf-8')).hexdigest())

        if output == 'compile':
            yara_data = yara.compile(source=rules)
        else:
            yara_data = rules

        f = open(folder + "/" . yara_hash + ".yara", 'w')
        f.write(yara_data)
        f.close

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract yara rules from eCrimeLabs broker service')
    parser.add_argument("-t", "--type", required=True, type=str, default='any', help="incident, block, alert or any")
    parser.add_argument("-a", "--age",  required=True, type=str, default='1y', help="1h, 2h, 12h, 1d, 2d, 1w, 1m, 2m, 3m, 4m, 5m, 6m, 1y, 2y, 4y or 10y")
    parser.add_argument("-o", "--output", required=True, type=str, default='1y', help="plain or compile")
    parser.add_argument("-f", "--folder", required=True, type=str, default='broker_yara', help="Folder for the output yara files")
    args = parser.parse_args()

    if not args.type in ['incident', 'block', 'alert', 'any']:
        print ("The type \"" + args.type + "\" is not a valud type")
        exit()
    if not args.age in ['1h', '2h', '12h', '1d', '2d', '1w', '1m', '2m', '3m', '4m', '5m', '6m', '1y', '2y', '4y', '10y']:
        print ("The age \"" + args.age + "\" is not a valid age")
        exit()
    if not args.output in ['plain', 'compile']:
        print ("The output \"" + args.output + "\" is not valid output")
        exit()

    json_object = fetch_broker_data(args.type, args.age)
    if(json_validator(json_object)):
        parse_json_object(json_object, args.output, args.folder)
    else:
        print ("The validation of the fetched json object failed")
