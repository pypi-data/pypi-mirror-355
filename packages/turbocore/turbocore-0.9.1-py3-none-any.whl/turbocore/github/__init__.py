import os
import requests
from rich.pretty import pprint as PP
import time


def base_url():
    return "https://api.github.com"


def hdr():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % os.environ.get("TC_GHT", "missing-token-in-env-TC_GHT")
    }


def gh_repo():
    x = requests.get(base_url() + "/user/repos?affiliation=collaborator", headers=hdr())
    PP(x.json())

def gh_me():
    x = requests.get(base_url() + "/user", headers=hdr())
    PP(x.json())

def gh_rate():
    x = requests.get(base_url() + "/rate_limit", headers=hdr()).json()
    all_used = {}
    for k in x["resources"].keys():
        all_used[k] = x["resources"][k]["used"]
    all_used["rate"] = x["rate"]["used"]
    #sorted keys
    sks = list(sorted(all_used.keys()))
    cols = []
    for k in sks:
        cols.append("%d" % all_used[k])
    
    sks.insert(0, "epoch")
    cols.insert(0, "%d" % int(time.time()))

    print(",".join(sks))
    print(",".join(cols))


def main():
    import turbocore
    turbocore.cli_this(__name__, 'gh_')
