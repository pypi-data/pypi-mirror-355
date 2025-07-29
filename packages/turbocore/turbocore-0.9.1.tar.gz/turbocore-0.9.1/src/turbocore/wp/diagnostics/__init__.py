from rich.pretty import pprint as PP
import subprocess
import json
import os
import sys
import xler8


def shotgun(data_with_headers, filename_prefix, sheet_name, separate_columns=None):
    """Output in 5 file formats, xlsx, csv(comma), scsv(semicolon), tsv(tabs), ssv(space) and individual columns on demand."""
    titles = data_with_headers[0]
    rows = data_with_headers[1:]

    # xlsx
    xler8.out(filename_prefix + ".xlsx", sheets={
        sheet_name: {
            'data': data_with_headers,
            'cw': xler8.cw_gen(data_with_headers)
        }
    })

    #tsv
    with open(filename_prefix + ".tsv", "w") as f:
        f.write("\t".join(titles))
        f.write("\n")
        for row in rows:
            f.write("\t".join(row))
            f.write("\n")

    #csv
    with open(filename_prefix + ".csv", "w") as f:
        f.write(",".join(titles))
        f.write("\n")
        for row in rows:
            f.write(",".join(row))
            f.write("\n")

    #scsv
    with open(filename_prefix + ".scsv", "w") as f:
        f.write(";".join(titles))
        f.write("\n")
        for row in rows:
            f.write(";".join(row))
            f.write("\n")

    #ssv
    with open(filename_prefix + ".ssv", "w") as f:
        f.write(" ".join(titles))
        f.write("\n")
        for row in rows:
            f.write(" ".join(row))
            f.write("\n")

    if separate_columns != None:
        for title in separate_columns:
            idx = titles.index(title)
            with open(filename_prefix + ".%s.txt" % title, "w") as f:
                for row in rows:
                    f.write(row[idx])
                    f.write("\n")


def get_base_cmd():
    return '''/usr/local/bin/wp --allow-root --path=/var/www/html '''


def remote_wp(wp_cli_cmd, as_json=False):
    host = get_ssh_host()
    base_cmd = get_base_cmd()
    lines = subprocess.check_output(envelope_ssh(host, base_cmd + wp_cli_cmd), shell=True, universal_newlines=True).strip().split("\n")
    if json:
        try:
            return json.loads("\n".join(lines))
        except Exception as e:
            print(str(e))
            return None
    return lines


def envelope_ssh(host, local_cmd):
    return '''ssh -q %s "%s"''' % (host, local_cmd)


def wp_users():
    fields_s="ID,user_login,user_email,user_registered,user_status,roles"
    fields = fields_s.split(",")
    src_data = remote_wp(wp_cli_cmd="user list --format=json --fields=%s" % fields_s, as_json=True)
    data = [fields]
    for user in src_data:
        row=[]
        for f in fields:
            row.append(str(user[f]))
        data.append(row)
    shotgun(data_with_headers=data, filename_prefix="users", sheet_name="users", separate_columns=["ID"])
    sys.exit(0)


def get_user_meta_list(user_id:int):
    # o_only_keys = ""
    # if only_keys is not None:
    #     o_only_keys = " --keys=" + ",".join(only_keys)
    reso = remote_wp(
        wp_cli_cmd="user meta list %d --format=json" % (user_id),
        as_json=True
        )
    data = [["user_id", "meta_key", "meta_value"]]
    for item in reso:
        data.append([str(item["user_id"]),str(item["meta_key"]),str(item["meta_value"])])
    return data


def wp_test(p1:str, p2:str, p3:str):
    """Test Funktion."""
    print("p1=%s" % p1)
    print("p2=%s" % p2)
    print("p3=%s" % p3)
    print("will use " + get_ssh_host())
    sys.exit(0)

def wp_usermeta(id_filename, tsv_outfile):
    user_ids = [ int(x) for x in open(id_filename, 'r').read().strip().split("\n")]
    from rich.progress import track
    with open(tsv_outfile, 'w') as f:
        f.write("\t".join(["user_id", "meta_key", "meta_value"]))
        f.write("\n")
    for user_id in track(user_ids, description="Loading User Meta values..."):
        reso = get_user_meta_list(user_id=user_id)
        with open(tsv_outfile, 'a') as f:
            for row in reso[1:]:
                f.write("\t".join(row))
                f.write("\n")
    sys.exit(0)


def get_ssh_host():
    return os.environ.get("WHIPPED_HOST", "werkstatt")


def main():
    import turbocore
    turbocore.cli_this(__name__, 'wp_')
    return

    host = "werkstatt"

    #users = wp_user_list(host)
    um = wp_user_meta_list(host, 1, only_keys=["nickname"])

    print("*"*80)
    # PP(users)
    PP(um)
    print("*"*80)
