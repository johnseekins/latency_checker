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
RANDOM = True
DEBUG = False
PREFIX = "endpoints"

def opts():
    args = argparse.ArgumentParser("Options for Latency Checker")
    args.add_argument("-c", "--config", help="JSON config file",
                      required=True, dest="config")
    args.add_argument("-d", "--debug", help="Debug Info",
                      default=False, dest="debug")
    return args.parse_args()


def check_site(sitedict):
    name = sitedict['name']
    protocol = sitedict['protocol']
    uri = sitedict['uri']
    site = "%s%s" % (protocol, uri)
    if DEBUG:
        print("Checking %s" % name)
    try:
        r = requests.get(site, timeout=TIMEOUT)
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
DEBUG = config.get('debug', False)
PREFIX = config.get('prefix', 'endpoints')
if args.debug:
    DEBUG = True

num_sites = len(config['sites'])
avgs = {}
for i in xrange(3):
    if DEBUG:
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
                val = float((avgs[name][0] + val) / 2)
            avgs[name] = (val, True)
    if DEBUG:
        print("Current latency stats: %s" % avgs)
        print("Taking a quick break...")
    sleep(num_sites / 2)

send_string = ""
t = time()
host = config.get("hostname", node())
avg = 0
count = 0
for endpoint, value in avgs.iteritems():
    val, worked = value
    if worked:
        tmp_string = "%s.%s.%s.response-ms %d %d\n" % (PREFIX, host,
                                                       endpoint, val, t)
        send_string += tmp_string
        count += 1
        avg += val
    else:
        print("Skipping %s because it failed" % endpoint)

if send_string:
    avg = float(avg / count)
    send_string += "%s.%s.avg_latency-ms %d %d\n" % (PREFIX, host, avg, t)

print("Collected:\n%s" % send_string)

if all(k in config for k in ['server', 'port']) and send_string:
    print("Sending to metrics endpoint %s::%s" % (config['server'],
                                                  config['port']))
    sock = socket.socket()
    sock.connect((config['server'], config['port']))
    sock.sendall(send_string)
    sock.close()

