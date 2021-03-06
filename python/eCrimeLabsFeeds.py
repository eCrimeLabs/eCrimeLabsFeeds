#!/usr/bin/python3
"""
 The following script can be used to fetch IOC data from the eCrimeLabs Broker API
 and stores it into files or bulk can be choosen.

    Sample usage:
     python3 eCrimeLabsFeeds.py -h
     python3 eCrimeLabsFeeds.py --listtypes
     python3 eCrimeLabsFeeds.py --output /home/<user>/iocs/ --feed any --age 1d --bulk
     python3 eCrimeLabsFeeds.py --output temp1 --feed block --age 1d --type ipv4
     python3 eCrimeLabsFeeds.py --server 127.0.0.1 --port 11211 --expiration 600 --feed alert --age 2d --type ipv4

---------------------------------------------------------------------------

MIT License

Copyright (c) 2019 Dennis Rand (https://www.ecrimelabs.com)

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
import os
import datetime
import memcache
from pprint import pprint
from keys import broker_url, broker_key

def splash():
    print ("\r\n")
    print ('eCrimeLabs Broker Feed/Module IOC extractor')
    print ('(c)2019 eCrimeLabs')
    print ('https://www.ecrimelabs.com')
    print ("----------------------------------------\r\n")


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

def check_file_writable(fnm):
    if os.path.exists(fnm):
        # path exists
        if (os.path.isfile(fnm)): # is it a file or a dir?
            # also works when file is a link and the target is writable
            return os.access(fnm, os.W_OK)
        else:
            return False # path is a dir, so cannot write as a file

    # target does not exist, check perms on parent dir
    pdir = os.path.dirname(fnm)
    if not pdir: pdir = '.'
    # target is creatable if parent dir is writable
    return os.access(pdir, os.W_OK)

def get_data_from_api(url, type):
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

def fetch_data_from_module(output, module):
    global broker_url
    global broker_key

    if not (check_file_writable(output)):
        print ("An error occoured in relation to creating file " + output)
        sys.exit(1)

    moduleslist  = list_api_content("listmodules")
    valid = False
    for modulelist in moduleslist:
        if (modulelist == module):
            valid = True
    if not (valid):
        print ("The module " + module + " does not exists")
        sys.exit()

    url = broker_url + "/feed/" + module + "/" + broker_key

    filedata = (get_data_from_api(url, "module"))

    filebuffer = open(output, 'w')
    filebuffer.write(filedata + "\r\n")
    filebuffer.close
    return (output)

def fetch_data_from_api_memcache(output, feeds, types, age, server, port, expiration):
    global broker_url
    global broker_key

    try:
       client = memcache.Client([server + ':' + port], debug=0)
       client.set("connection-test", "eCrimeLabsFeed-test", 2)
       output = client.get("connection-test")
       if (output is None):
          print ("Failed to write/read from Memcached server: " + server + ":" + port)
          sys.exit()
    except:
        print ("Failed to connect to Memcached server: " + server + ":" + port)
        sys.exit()

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

    url = broker_url + "/apiv1/" + feeds + "/" + types + "/" + age + "/" + broker_key + "/txt"

    feed_data = (get_data_from_api(url, "feed"))
    feed_data = re.sub(r"^#\sChecksum.*", "", feed_data, 0, re.IGNORECASE | re.MULTILINE)
    feed_data = re.sub("^\n", "", feed_data, 0, re.IGNORECASE | re.MULTILINE)

    entries = feed_data.split('\r\n')
    cnt = 0
    for entry in entries:
        if not len(entry.strip()) == 0 :
           client.set(types + "-" + entry, "eCrimeLabsFeed", int(expiration))
           print ("Adding: " + entry)
           cnt += 1

    print ("-----------------------")
    print ("Added: " + str(cnt) + " entries to memcached")
    return (str(cnt))


def fetch_data_from_api_fs(output, feeds, types, age, bulk):
    global broker_url
    global broker_key

    if(bulk): # Folder
        if not (check_directory_writable(output)):
            print ("An error occoured in relation to writting to folder " + output)
            sys.exit(1)
    else: # File
        if not (check_file_writable(output)):
            print ("An error occoured in relation to creating file " + output)
            sys.exit(1)

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

    filedata = (get_data_from_api(url, "feed"))

    if(bulk):
        if output.endswith('/'):
            output = output[:-1]

        output = output + "/" + feeds + "_" + types + ".csv"
    filebuffer = open(output, 'w')
    filebuffer.write("# Date: " + now.strftime("%Y-%m-%d %H:%M:%S") + " UTC\r\n")
    filebuffer.write("# Feed: " + feeds + "\r\n")
    filebuffer.write("# Type: " + types + "\r\n")
    filebuffer.write("# Age: " + age + "\r\n")
    filebuffer.write(filedata + "\r\n")
    filebuffer.close
    return (output)



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
    parser.add_argument("--listmodules",  help="Displays a list of avaliable modules", action='store_true')
    parser.add_argument("-o", "--output", help="Output file and if used in conjunction with --bulk it has to be folder")
    parser.add_argument("-t", "--type", help="Defined the type of data")
    parser.add_argument("-f", "--feed", help="Defined the feed from where to get data from")
    parser.add_argument("-a", "--age", help="Defined the age to go back in time to fetch data from (default 1 hour)", default="1h")
    parser.add_argument("-b", "--bulk", help="Fetches all the types of a specific feed into a folder", action='store_true')
    parser.add_argument("-m", "--module", help="Fetches data content of a module")
    parser.add_argument("-e", "--expiration", help="Memcached expiration of data in seconds (default 10 minutes)", default="600")
    parser.add_argument("-s", "--server", help="Memcached server (default 127.0.0.1)", default="127.0.0.1")
    parser.add_argument("-p", "--port", help="Memcached server port (default 11211)", default="11211")
    if len(sys.argv)==1:
    	parser.print_help(sys.stderr)
    	sys.exit(1)
    args = parser.parse_args()

    if (args.listfeeds):
        print (" [*] Listing avaliable feeds from API...")
        outputs = list_api_content("listfeeds")
        for output in outputs:
            print ("\t - " + str(output))
        sys.exit()
    elif (args.listtypes):
        print (" [*] Listing avaliable types from API...")
        outputs = list_api_content("listtypes")
        for output in outputs:
            print ("\t " + output)
        sys.exit()
    elif (args.listages):
        print (" [*] Listing avaliable ages from API...")
        outputs = list_api_content("listages")
        for output in outputs:
            print ("\t " + output)
        sys.exit()
    elif (args.listmodules):
        print (" [*] Listing avaliable modules from API...")
        outputs = list_api_content("listmodules")
        for output in outputs:
            print ("\t " + output)
        sys.exit()

    else:
        if (args.module and args.output):
            print (" [*] Fetching module data feeds from API initiated")
            print ("   [-] Save to file: " + args.output)
            print ("----------------------------------------\r\n")
            fetch_data_from_module_fs(args.output, args.module)
        elif (args.output and args.type and args.feed and args.age and not args.bulk):
            print (" [*] Fetching IOCs from API initiated")
            print ("   [-] Feed: " + args.feed)
            print ("   [-] Type: " + args.type)
            print ("   [-] Age: " + args.age)
            print ("   [-] Save to file: " + args.output)
            print ("----------------------------------------\r\n")
            fetch_data_from_api_fs(args.output, args.feed, args.type, args.age, args.bulk)
        elif (args.output and args.feed and args.age and args.bulk and not args.type):
            print (" [*] Fetching bulk IOCs from API initiated")
            print ("   [-] Feed: " + args.feed)
            print ("   [-] Type: all")
            print ("   [-] Age: " + args.age)
            print ("   [-] Saving to folder: " + args.output)
            print ("----------------------------------------\r\n")
            data_types = list_api_content("listtypes")
            print ("    [-] Writting data files: ")
            for data_type in data_types:
                filename = fetch_data_from_api_fs(args.output, args.feed, data_type, args.age, args.bulk)
                if os.path.exists(filename):
                    print("      + " + filename)
        elif (args.server and args.port and args.expiration and args.feed and args.age and args.type):
            print (" [*] Fetching IOCs from API initiated")
            print ("   [-] Feed: " + args.feed)
            print ("   [-] Type: " + args.type)
            print ("   [-] Age: " + args.age)
            print ("   [-] Store into Memcached: " + args.server + " on port " + args.port)
            print ("   [-] Memcached expiration: " + args.expiration + " seconds")
            print ("----------------------------------------\r\n")
            fetch_data_from_api_memcache(args.output, args.feed, args.type, args.age, args.server, args.port, args.expiration)

        else:
            parser.print_help(sys.stderr)
            sys.exit(1)
