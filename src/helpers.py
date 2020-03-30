import requests
import os
from zipfile import ZipFile
from supermicro import Supermicro
import shutil
import re


BMC_FILENAME_PATTERN = r"^[\w\-. ]+\.(bin|BIN)$"
"""
********* BIOS Naming Convention **********

BIOS name  : PPPPPSSY.MDD
PPPPP      : 5-Bytes for project name
SS         : 2-Bytes supplement for PPPPP (if applicable)
Y          : Year, 4 -> 2014, 5-> 2015, 6->2016
MDD        : Month + Date, for months, A -> Oct., B -> Nov., C -> Dec.

E.g., For BIOS with the build date, 2/18/2017:
        X11DPU+  -> X11DPU7.218
        X11DPi-T -> X11DPi7.218
"""
BIOS_FILENAME_PATTERN = r"^[\w\-. ]+\.([A-Ca-C]\d{2}|\d{3}|\d{3}_\w{3})$"


def download_file(url, path_to):
    file_name = url.split("/")[-1].strip()
    print("[*] Downloading {0} to {1}".format(file_name, path_to))
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        if not os.path.exists(path_to):
            os.makedirs(path_to)
        file_path = os.path.join(path_to, file_name)
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print("[*] Download finished")
        return file_name
    else:
        return None


def mk_board_dir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    except OSError as err:
        print(err.strerror)


def extract_zip(zipfile="", path_from=""):
    """
    Recursive extract Zip file
    """
    filepath = path_from + zipfile
    extract_path = filepath.strip(".zip") + "/"
    parent_archive = ZipFile(filepath)
    parent_archive.extractall(extract_path)
    namelist = parent_archive.namelist()
    parent_archive.close()
    for name in namelist:
        try:
            if name[-4:] == ".zip":
                extract_zip(zipfile=name, path_from=extract_path)
        except:  # noqa
            print("[!] Failed to extract ", name)
            pass
    return extract_path


def locate_and_move(dir_from, dir_to, pattern):
    for root, _dirs, files in os.walk(dir_from):
        for file in files:
            res = re.match(pattern, file)
            if res:
                filename = os.path.join(root, file)
                shutil.copy(filename, dir_to)
                return os.path.join(dir_to, file)


def get_bios(board_model):
    # Search for the most recent bios on supermicro website
    smc = Supermicro()
    biosupdater = smc.get_bios(board_model)
    smc.close()
    if not biosupdater:
        error = f"Could not find a valid Bios file for this board [{board_model}].\n"
        error += "Please visit supermicro motherboard page for more information."
        print(error)
        return None

    # Download the file
    url = biosupdater.link
    dl_path = f"/tmp/downloads/{board_model}/"
    bios_zip = download_file(url, dl_path)
    if not bios_zip:
        print("Failed to download the Bios File")
        return None

    # Recursive Extract the File
    extract_zip(bios_zip, dl_path)
    # Search for the BIOS file, and copy it to the bios folder
    bios_path = f"{board_model}/bios"
    mk_board_dir(bios_path)
    biosfile = locate_and_move(dl_path, bios_path, BIOS_FILENAME_PATTERN)
    return biosfile if biosfile else None


def get_bmc(board_model):
    # Search for the most recent bios on supermicro website
    smc = Supermicro()
    bmcupdater = smc.get_bmc(board_model)
    smc.close()
    if not bmcupdater:
        error = f"Could not find a valid BMC Firmware file for this board [{board_model}].\n"
        error += "Please visit supermicro motherboard page for more information."
        print(error)
        return None

    # Download the file
    url = bmcupdater.link
    dl_path = f"/tmp/downloads/{board_model}/"
    bios_zip = download_file(url, dl_path)
    if not bios_zip:
        print("Failed to download the BMC Firmware File")
        return None

    # Recursive Extract the File
    extract_zip(bios_zip, dl_path)
    # Search for the BMC file, and copy it to the bmc folder
    bmcpath = f"{board_model}/bmc"
    mk_board_dir(bmcpath)
    bmc_file = locate_and_move(dl_path, bmcpath, BMC_FILENAME_PATTERN)
    return bmc_file if bmc_file else None
