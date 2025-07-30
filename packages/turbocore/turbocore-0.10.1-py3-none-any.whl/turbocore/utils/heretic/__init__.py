import time
import pathlib
import turbocore
import json
import subprocess
from rich.pretty import pprint as PP
import inspect
import os
import os.path


CONST_SRC_BEGIN = "#+begin_src \n"
CONST_SRC_END = "#+end_src\n"


org_filename = None

def af(text):
    global org_filename
    with open(org_filename, 'a') as f:
        f.write(text)


def wf(filename, text):
    with open(filename, 'w') as f:
        f.write(text)


def count_versions():
    return 0


def heretic__systemsurgeon(ACTION, HOST, R_SRC, R_TYPE, INDIRECT_USER_MODE):
    """Backup or restore things.
    
    Parameters:
      ACTION (str)               : action to perform one of ['restore-0','backup','patch']
      HOST (str)                 : configured ssh user access
      R_SRC (str)                : remote path
      R_TYPE (str)               : remote path type, one of ['file', 'dir']
      INDIRECT_USER_MODE (str)   : one of ['root', 'sudo', 'user']

    Example Shell Script:      
      tss systemsurgeon backup HOST /etc/apache2/apache2.conf file sudo # version1=backup
      tss systemsurgeon backup HOST /etc/apache2/apache2.conf file sudo # version2=edit this before patch
      tss systemsurgeon patch HOST /etc/apache2/apache2.conf file sudo
      tss systemsurgeon restart HOST apache2 systemd sudo

    """
    args = inspect.getargvalues(inspect.currentframe()).locals # no other vars defined yet so sufficient
    global org_filename
    org_filename = os.path.join(HOST, "index.org")
    
    # for debugging only, see my named calling args
    PP(args)
    
    dir_dirs = os.path.join(HOST, "dirs")
    dir_files = os.path.join(HOST, "files")
    
    if not os.path.isdir(HOST):
        os.makedirs(HOST)
        af("* hostdir =%s= created\n\n" % HOST)

    os.makedirs(dir_dirs, exist_ok=True)
    os.makedirs(dir_files, exist_ok=True)

    r_src_id = R_SRC.replace("/", "_")
    r_src_local = R_SRC.split("/")[-1] # "file name only" in remote directory

    T=int(time.time())

    if ACTION == "restart" and R_TYPE == "systemd":
        
        if INDIRECT_USER_MODE == "sudo":

            af("* Restarting =%s=\n\n" % R_SRC)
            
            af("** Status OLD\n\n")
            af(CONST_SRC_BEGIN)
            status_stdout = subprocess.check_output("""ssh %s 'sudo systemctl status %s 2>&1' ; exit 0""" % (HOST, R_SRC), shell=True, universal_newlines=True)
            af(status_stdout)
            af(CONST_SRC_END)
            af("\n\n")

            af("** Restart Output (STDERR+STDOUT)\n\n")
            af(CONST_SRC_BEGIN)
            restart_stdout = subprocess.check_output("""ssh %s 'sudo systemctl restart %s 2>&1' ; exit 0""" % (HOST, R_SRC), shell=True, universal_newlines=True)
            af(restart_stdout)
            af(CONST_SRC_END)
            af("\n\n")
    
            af("** Status NEW\n\n")
            af(CONST_SRC_BEGIN)
            status_stdout = subprocess.check_output("""ssh %s 'sudo systemctl status %s 2>&1' ; exit 0""" % (HOST, R_SRC), shell=True, universal_newlines=True)
            af(status_stdout)
            af(CONST_SRC_END)
            af("\n\n")
    
    if ACTION == "patch" and R_TYPE == "file":
        
        if INDIRECT_USER_MODE == "sudo":
            #find latest item_dir_t
            item_dir = os.path.join(dir_files, r_src_id)
            item_dir_obj = pathlib.Path(item_dir)
            all_versions = []
            for d in item_dir_obj.iterdir():
                if d.is_dir():
                    all_versions.append(d.name)

            if len(all_versions) < 2:
                raise Exception("I refuse to patch [%s], you have no local backup." % (R_SRC))

            v0 = list(sorted(all_versions))[0]
            latest = list(sorted(all_versions))[-1]
            diff_filename = os.path.join(dir_files, r_src_id, 'latest.diff')
            my_local_v0_data_filename = os.path.join(dir_files, r_src_id, v0, r_src_local)
            my_local_data_filename = os.path.join(dir_files, r_src_id, latest, r_src_local)
            
            
            subprocess.check_output("diff -u %s %s >%s ; exit 0" % (my_local_v0_data_filename, my_local_data_filename, diff_filename), shell=True, universal_newlines=True)


            af("* Patch =%s=\n\n" % R_SRC)

            af("** Changes (Between backup and latest)\n\n")
            af(CONST_SRC_BEGIN)
            with open(diff_filename, 'r') as f_diff:
                af(f_diff.read())
            af(CONST_SRC_END)
            af("\n\n")

            cmd_upload = """rsync --rsync-path='sudo rsync' -avz %s %s:%s 2>&1""" % (my_local_data_filename, HOST, R_SRC)

            af("** Rsync Upload Output\n\n")
            af(CONST_SRC_BEGIN)
            upload_output = subprocess.check_output(cmd_upload, shell=True, universal_newlines=True)
            af(upload_output)
            af(CONST_SRC_END)
            af("\n\n")


    if ACTION == "backup" and R_TYPE == "file":
        time.sleep(2) # for unique timestamps

        if INDIRECT_USER_MODE == "sudo":
            item_dir = os.path.join(dir_files, r_src_id)
            item_filename_SRC = os.path.join(dir_files, r_src_id, "SRC")
            item_dir_t = os.path.join(dir_files, r_src_id, "%d" % T)
            os.makedirs(item_dir_t)
            wf(item_filename_SRC, R_SRC)
            item_filename_DATA = os.path.join(item_dir_t, r_src_local)
            sudo_part="--rsync-path='sudo rsync'"
            download_output = subprocess.check_output("""rsync %s -avz %s:%s %s 2>&1""" % (sudo_part, HOST, R_SRC, item_filename_DATA), shell=True, universal_newlines=True)


            item_dir_obj = pathlib.Path(item_dir)
            all_versions = []
            for d in item_dir_obj.iterdir():
                if d.is_dir():
                    all_versions.append(d.name)


            af("* Backup of =%s=\n\n" % R_SRC)
            af("** Local Location (Version %d)\n\n" % len(all_versions))
            af(CONST_SRC_BEGIN)
            af(item_filename_DATA + "\n")
            af(CONST_SRC_END)
            af("\n\n")
            
            af("** Rsync output\n\n")
            af(CONST_SRC_BEGIN)
            af(download_output)
            af(CONST_SRC_END)
            af("\n\n")


    if ACTION == "backup" and R_TYPE == "dir":
        time.sleep(2) # for unique timestamps
        
        if INDIRECT_USER_MODE == "sudo":
            item_dir = os.path.join(dir_dirs, r_src_id)
            item_filename_SRC = os.path.join(dir_dirs, r_src_id, "SRC")
            item_dir_t = os.path.join(dir_dirs, r_src_id, "%d" % T)
            os.makedirs(item_dir_t)
            wf(item_filename_SRC, R_SRC)
            #item_filename_DATA = os.path.join(item_dir_t, r_src_local)
            sudo_part="--rsync-path='sudo rsync'"
            # see /. in command src
            # see universal...=False for wrong unicode chars in command
            subprocess.check_output("""rsync %s -avz %s:%s/. %s""" % (sudo_part, HOST, R_SRC, item_dir_t), shell=True, universal_newlines=False)


def heretic__test():
    pass


def main():
    turbocore.cli_this(__name__, "heretic__")
