#!/usr/bin/env python
import requests
import socket
from json import load
from time import time, sleep
from platform import node
from multiprocessing import Pool, cpu_count
from random import randrange
import argparse
TIMEOUT = 10


def opts():
    args = argparse.ArgumentParser("Options for Latency Checker")
    args.add_argument("-c", "--config", help="JSON config file",
                      required=True, dest="config")
    return args.parse_args()


def check_site(sitedict):
    name = sitedict['name']
    protocol = sitedict['protocol']
    uri = sitedict['uri']
    site = "%s%s" % (protocol, uri)
    print("Checking %s" % name)
    r = requests.get(site, timeout=10)
    if r.status_code != 200:
        print("Failed to get %s correctly" % name)
    # milliseconds
    uri = uri.replace('.', '_')
    uri = uri.replace('/', '_')
    return (uri, r.elapsed.total_seconds() * 1000)

args = opts()
try:
    with open(args.config, 'r') as f_in:
        config = load(f_in)
except Exception, e:
    print("Couldn't load config :: %s" % e)
    exit(1)

TIMEOUT = config.get('timeout', 10)
RANDOM = config.get('random', True)

num_sites = len(config['sites'])
avgs = {}
for i in xrange(3):
    print("Round %d" % (i + 1))
    if RANDOM:
        # avoid picking '0'
        p = Pool(randrange(num_sites) + 1)
    else:
        p = Pool(cpu_count())
    cur_lat = p.map(check_site, config['sites'])
    for lat in cur_lat:
        if lat[0] in avgs:
           avgs[lat[0]] = (avgs[lat[0]] + lat[1]) / 2
        else:
           avgs[lat[0]] = lat[1]
    print("Taking a quick break...")
    sleep(num_sites / 2)

print("Avg. Latencies: %s" % avgs)

send_string = ""
t = time()
host = config.get("hostname", node())
for endpoint, value in avgs.iteritems():
    tmp_string = "endpoints.%s.%s.response-ms %d %d\n" % (host, endpoint,
                                                          value, t)
    send_string += tmp_string

if all(k in config for k in ['server', 'port']):
    sock = socket.socket()
    sock.connect((config['server'], config['port']))
    sock.sendall(send_string)
    sock.close()

