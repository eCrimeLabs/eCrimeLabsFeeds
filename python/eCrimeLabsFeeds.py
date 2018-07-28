#!/usr/bin/python3
"""
 The following script can be used to fetch feed data from the eCrimeLabs Broker API
 and stores it into seperate files.


MIT License

Copyright (c) 2018 Dennis Rand (https://www.ecrimelabs.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import re
import sys
import requests
import argparse
import string
import json
import os.path
import datetime
from pprint import pprint
from keys import broker_url, broker_key

def splash():
    print ('eCrimeLabs Broker Feed')
    print ('(c)2018 eCrimeLabs')
    print ('https://www.ecrimelabs.com')
    print ("----------------------------------------\r\n")

def check_file_writable(fnm):
    if os.path.exists(fnm):
        # path exists
        if os.path.isfile(fnm): # is it a file or a dir?
            # also works when file is a link and the target is writable
            return os.access(fnm, os.W_OK)
        else:
            return False # path is a dir, so cannot write as a file
    # target does not exist, check perms on parent dir
    pdir = os.path.dirname(fnm)
    if not pdir: pdir = '.'
    # target is creatable if parent dir is writable
    return os.access(pdir, os.W_OK)

def get_data_from_api(url):
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
        outputs = "# Checksum of below data: " + r.headers.get('X-body-checksum') + "\r\n"
        outputs += r.text
        return (outputs)
    else:
        print ("Error occoured when listing API content")
        sys.exit()

def validate_data_for_api(output, feeds, types, age):
    global broker_url
    global broker_key

    if not (check_file_writable(output)):
        print ("An error occoured in relation to creating file " + output)
        sys.exit()

    # Fetches the different data types to ensure that the requests made are correct
    feedslist = list_api_content("listfeeds")
    valid = False
    for feedlist in feedslist:
        if (feedlist == feeds):
            valid = True
    if not (valid):
        print ("The feed value " + feeds + " is not a valid Feed")
        sys.exit()

    typeslist = list_api_content("listtypes")
    valid = False
    for typelist in typeslist:
        if (typelist == types):
            valid = True
    if not (valid):
        print ("The type value " + types + " is not a valid Type")
        sys.exit()

    ageslist  = list_api_content("listages")
    valid = False
    for agelist in ageslist:
        if (agelist == age):
            valid = True
    if not (valid):
        print ("The age value " + age + " is not a valid Age")
        sys.exit()

    now = datetime.datetime.now(datetime.timezone.utc)
    url = broker_url + "/apiv1/" + feeds + "/" + types + "/" + age + "/" + broker_key + "/txt"
    filedata = (get_data_from_api(url))

    filebuffer = open(output, 'w')
    filebuffer.write("# Date: " + now.strftime("%Y-%m-%d %H:%M:%S") + " UTC\r\n")
    filebuffer.write("# Feed: " + feeds + "\r\n")
    filebuffer.write("# Type: " + types + "\r\n")
    filebuffer.write("# Age: " + age + "\r\n")
    filebuffer.write(filedata + "\r\n")
    filebuffer.close

def list_api_content(content):
    global broker_url
    global broker_key
    url = broker_url + '/apiv1/' + content + '/' + broker_key

    try:
        r = requests.get(url,timeout=5)
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
        outputs = r.json()
        return(outputs)
    else:
        print ("Error occoured when listing API content")
        sys.exit()

if __name__ == '__main__':
    splash()
    parser = argparse.ArgumentParser()
    parser.add_argument("--listtypes", help="Displays a list of valid types to use", action='store_true')
    parser.add_argument("--listfeeds", help="Displays a list of valid feeds to use", action='store_true')
    parser.add_argument("--listages",  help="Displays a list of valid ages to use", action='store_true')
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("-t", "--type", help="Defined the type of data")
    parser.add_argument("-f", "--feed", help="Defined the feed from where to get data from")
    parser.add_argument("-a", "--age", help="Defined the age to go back in time to fetch data from (default 1 hour)", default="1h")
    if len(sys.argv)==1:
    	parser.print_help(sys.stderr)
    	sys.exit(1)
    args = parser.parse_args()

    if (args.listfeeds):
        print (" - Fetching " + args.listfeeds + " from API...")
        outputs = list_api_content("listfeeds")
        for output in outputs:
            print ("\t " + output)
        sys.exit()
    elif (args.listtypes):
        print (" - Fetching " + args.listtypes + " from API...")
        outputs = list_api_content("listtypes")
        for output in outputs:
            print ("\t " + output)
        sys.exit()
    elif (args.listages):
        print (" - Fetching " + args.listages + " from API...")
        outputs = list_api_content("listages")
        for output in outputs:
            print ("\t " + output)
        sys.exit()
    else:
        if (args.output and args.type and args.feed and args.age):
            validate_data_for_api(args.output, args.feed, args.type, args.age)
        else:
            parser.print_help(sys.stderr)
            sys.exit(1)
