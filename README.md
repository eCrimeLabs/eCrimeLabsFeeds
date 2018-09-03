# eCrimeLabsFeeds
A tool to fetch all the feeds presented through the API

The following script can be used to fetch IOC data from the eCrimeLabs Broker API
and stores it into files or bulk can be choosen.

   Sample usage:
```
    python3 eCrimeLabsFeeds.py -h
    python3 eCrimeLabsFeeds.py --listtypes
    python3 eCrimeLabsFeeds.py --output /home/<user>/iocs/ --feed any --age 1d --bulk
    python3 eCrimeLabsFeeds.py --output temp1 --feed block --age 1d --type ipv4
```

Remember to create the file "keys.py" should look like this:
```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

broker_url = 'https://broker_url'
broker_key = '00000000-0000-0000-0000-000000000000'
```
