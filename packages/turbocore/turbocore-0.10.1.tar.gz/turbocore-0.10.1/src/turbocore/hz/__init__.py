import turbocore
import json
from hcloud import Client
import os
import sys
import time
import requests
import rich
from rich.pretty import pprint as PP
import datetime
import subprocess


g_token = None
g_token_ns = None


g_client = None
g_client_ns = None


def load_clients():
    global g_client
    global g_client_ns
    global g_token
    global g_token_ns
    g_token = os.environ.get("HZ_TOKEN", "")
    if g_token != "":
        g_client = Client(token=g_token)
    g_token_ns = os.environ.get("HZ_TOKEN_NS", "")
    if g_token_ns != "":
        g_client_ns = Client(token=g_token_ns)

    if g_client is None and g_client_ns is None:
        raise Exception("No Clients initalized")



def hz_ip4():
    load_clients()
    servers = g_client.servers.get_all()
    res = []
    for server in servers:
        i = "%d" % server.id
        n = server.name
        ip4 = server.public_net.ipv4.ip
        row = [n, i, ip4]
        res.append(row)
    # sort lowercase first column = name
    res = sorted(res, key=lambda x: x[0].lower())
    for row in res:
        print("\t".join(row))

def hz_lb():
    load_clients()
    lbs = g_client.load_balancers.get_all()
    res = []
    for lb in lbs:
        PP(lb)
        break


def hz_lbdo():
    data = json.loads(subprocess.check_output("/bin/bash -c 'doctl compute load-balancer list -o json'", shell=True, universal_newlines=True))
    PP(data)


def hz_ip4do():
    data = json.loads(subprocess.check_output("/bin/bash -c 'doctl compute droplet list -o json'", shell=True, universal_newlines=True))
    #PP(data)
    res = []
    for server in data:
        i = "%d" % server["id"]
        n = server["name"]
        v4nets = server["networks"]["v4"]
        ip4 = ""
        for v4net in v4nets:
            if v4net["type"] == "public":
                ip4 = v4net["ip_address"]
        row = [n, i, ip4]
        res.append(row)
    res = sorted(res, key=lambda x: x[0].lower())
    for row in res:
        print("\t".join(row))


def main():
    turbocore.cli_this(__name__, "hz_")
