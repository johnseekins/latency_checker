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
    try:
        r = requests.get(site, timeout=10)
    except Exception, e:
        print("Connection to %s failed :: %s" % (name, e))
        return (uri, -1, False)
    if r.status_code != 200:
        print("Host: %s :: Status: %s" % (name, r.status_code))
        return (uri, -1, False)
    # milliseconds
    uri = uri.replace('.', '_')
    uri = uri.replace('/', '_')
    return (uri, r.elapsed.total_seconds() * 1000, True)

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
        name, val, worked = lat
        exists = avgs.get(name, False)
        if not worked:
            avgs[name] = (-1, False)
        else:
            if exists:
                avgs[lat[0]][0] = (avgs[lat[0]] + lat[1]) / 2
            else:
                avgs[lat[0]] = (lat[1], True)
    print("Taking a quick break...")
    sleep(num_sites / 2)

print("Avg. Latencies: %s" % avgs)

send_string = ""
t = time()
host = config.get("hostname", node())
for endpoint, value in avgs.iteritems():
    val, worked = value
    if worked:
        tmp_string = "endpoints.%s.%s.response-ms %d %d\n" % (host, endpoint,
                                                              val, t)
        send_string += tmp_string

if all(k in config for k in ['server', 'port']) and send_string:
    sock = socket.socket()
    sock.connect((config['server'], config['port']))
    sock.sendall(send_string)
    sock.close()

