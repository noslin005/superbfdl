# -*- coding: utf-8 -*-

import re
import subprocess
from subprocess import CalledProcessError
import sys
import time


def execute(cmd, args):
    """
    run a shell command
    """
    try:
        command = "{0} {1}".format(cmd, args)
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,)
        output = ""
        while proc.poll() is None:
            out = proc.stdout.readline().strip()
            print("  " + out)
            output += out + "\n"
        return output
    except (Exception, CalledProcessError) as err:
        print(err)


def run_sum(ip, username, password, cmd):
    """
    Execute a supermicro sum command
    """

    args = f"-i {ip} -u {username} -p {password} -c {cmd}"
    sum_output = execute("sum", args)
    return sum_output


def sum_updateBios(ip, username, password, biosFile):
    cmd = f"UpdateBios --file {biosFile}"

