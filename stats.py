import requests
import json
import pprint

tests = ['duckduckgo-owned-server_yahoo_net', 'duckduckgo_com', 'ec2_ap-northeast-1_amazonaws_com', 'ec2_ap-northeast-2_amazonaws_com', 'ec2_ap-south-1_amazonaws_com', 'ec2_ap-southeast-2_amazonaws_com', 'ec2_ap-southeast-1_amazonaws_com', 'ec2_eu-central-1_amazonaws_com', 'ec2_eu-west-1_amazonaws_com', 'ec2_sa-east-1_amazonaws_com', 'ec2_us-east-1_amazonaws_com', 'ec2_us-west-1_amazonaws_com', 'google_com', 'yahoo_com', 'www_bing_com_images_explore']

pp = pprint.PrettyPrinter(indent=1)
URL = "http://54.70.111.229/render/?format=json&from="


def get_endpoints(days, func, count):
    top_endpoints = {}
    """
    Get each test as a separate dataframe
    """
    url_base = "%s-%dd&target=%s(" % (URL, days, func)
    for t in tests:
        if 'mostDeviant' in func:
            url = "%s%d, endpoints.*.%s.response-ms)" % (url_base, count, t)
        else:
            url = "%sendpoints.*.%s.response-ms, %d)" % (url_base, t, count)
        r = requests.get(url)
        r = r.json()
        for e in r:
            ep = e['target'].split('.')[1]
            if t in top_endpoints:
                top_endpoints[t].append(ep)
            else:
                top_endpoints[t] = [ep]
    return top_endpoints

"""
Which endpoints are slow (highest avg latency) most frequently in the sample
"""
top_endpoints = get_endpoints(5, "highestAverage", 4)
high_avg = {}
for k, v in top_endpoints.iteritems():
    for i in v:
        if i in high_avg.keys():
            high_avg[i]['count'] += 1
            high_avg[i]['slow_endpoints'].append(k)
        else:
            high_avg[i] = {}
            high_avg[i]['count'] = 1
            high_avg[i]['slow_endpoints'] = [k]

"""
Which endpoints are slow (most deviant) most frequently in the sample
"""
top_endpoints = get_endpoints(5, "mostDeviant", 4)
most_dev = {}
for k, v in top_endpoints.iteritems():
    for i in v:
        if i in most_dev.keys():
            most_dev[i]['count'] += 1
            most_dev[i]['slow_endpoints'].append(k)
        else:
            most_dev[i] = {}
            most_dev[i]['count'] = 1
            most_dev[i]['slow_endpoints'] = [k]

"""
Format and display
"""
print("Slow regions:")
for k, v in high_avg.iteritems():
    if k not in most_dev:
        continue
    print("\n****%s****" % k)
    url = "%s-5d&target=endpoints.%s.avg_latency-ms" % (URL, k)
    r = requests.get(url)
    r = r.json()
    datapoints = [d for d in r[0]['datapoints'] if d[0]]
    lat = float(sum([d[0] for d in datapoints]) / len(datapoints))
    print("Avg. Latency: %d ms" % lat)
    m = dict(most_dev[k])
    del most_dev[k]

    print("Endpoints with spikes:")
    slow_lat = [i for i in m['slow_endpoints']]
    for i in slow_lat:
        url = "%s-5d&target=endpoints.%s.%s.response-ms" % (URL, k, i)
        r = requests.get(url)
        r = r.json()
        datapoints = [d for d in r[0]['datapoints'] if d[0]]
        lat = float(sum([d[0] for d in datapoints]) / len(datapoints))
        pp.pprint({"Name": i, "Avg. Latency": lat})
    s = [i for i in v['slow_endpoints'] if i not in m['slow_endpoints']]
    if not s:
        continue
    print("Slow endpoints:")
    for name in s:
        url = "%s-5d&target=endpoints.%s.%s.response-ms" % (URL, k, name)
        r = requests.get(url)
        r = r.json()
        datapoints = [d for d in r[0]['datapoints'] if d[0]]
        lat = float(sum([d[0] for d in datapoints]) / len(datapoints))
        pp.pprint({"Name": name, "Avg. Latency": lat})

print("\nConnections that are solid, but have some spikes:")
print(", ".join(most_dev.keys()))

