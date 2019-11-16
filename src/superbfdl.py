#!/usr/bin/env python3
import argparse
import io
import os
import re
import shutil
from zipfile import ZipFile

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options


# BMC_FILENAME_PATTERN = r"^[\w,\s-]+\.(bin|BIN)$"
BMC_FILENAME_PATTERN = r"^[\w\-. ]+\.(bin|BIN)$"
# Match
# H11SSL9.808_D32
# H11DSTB9.729
BIOS_FILENAME_PATTERN = r"^[\w\-. ]+\.([A-Da-d]\d{2}|\d{3}|\d{3}_\w{3})$"


def get_lates_bios(board_model):
    try:
        link = f"https://www.supermicro.com/en/products/motherboard/{board_model}"
        driver.get(link)
        driver.find_element_by_xpath(
            '//a[@href="{0}"]'.format("javascript:document.biosForm.submit();")
        ).click()
        raw = driver.find_element_by_class_name("yui-skin-sam").text.split("\n")
        for line in raw:
            if "BIOS Revision:" in line:
                bios_version = line.split(":")[1].replace("R", "").strip()
                a = driver.find_element_by_partial_link_text(".zip")
                filename = a.text
                software_id = a.get_attribute("href").split("=")[-1]
                bios_dl_link = "https://www.supermicro.com/Bios/softfiles/{0}/{1}".format(
                    software_id, filename
                )

                if bios_version and bios_dl_link:
                    return (bios_dl_link, bios_version)
    except NoSuchElementException as err:
        print(f"[!] Could not find valid bios link for board {board_model}")
        print(err.msg)
        return None


def get_lates_bmc_firmware(board_model):
    try:
        link = f"https://www.supermicro.com/en/products/motherboard/{board_model}"
        driver.get(link)
        driver.find_element_by_xpath(
            '//a[@href="{0}"]'.format("javascript:document.IPMIForm.submit();")
        ).click()
        raw = driver.find_element_by_class_name("yui-skin-sam").text.split("\n")
        for line in raw:
            if "Firmware Revision:" in line:
                bios_version = line.split(":")[1].replace("R", "").strip()
                a = driver.find_element_by_partial_link_text(".zip")
                filename = a.text
                software_id = a.get_attribute("href").split("=")[-1]
                bios_dl_link = "https://www.supermicro.com/Bios/softfiles/{0}/{1}".format(
                    software_id, filename
                )

                if bios_version and bios_dl_link:
                    return (bios_dl_link, bios_version)
    except NoSuchElementException as err:
        print(f"Could not find valid bmc firmware link for board {board_model}")
        print(err.msg)
        return None


def download_file(url, dl_path):
    file_name = url.split("/")[-1].strip()
    print("[*] Downloading {0} to {1}".format(file_name, dl_path))
    resp = requests.get(url, stream=True)
    if resp.status_code == 200:
        file_path = os.path.join(dl_path, file_name)
        with open(file_path, "wb") as bfile:
            for chunk in resp.iter_content(chunk_size=1024):
                bfile.write(chunk)
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


def locate_and_move(dir_from, dir_to, pattern):
    for root, _dirs, files in os.walk(dir_from):
        for file in files:
            res = re.match(pattern, file)
            if res:
                filename = os.path.join(root, file)
                shutil.copy(filename, dir_to)
                return os.path.join(dir_to, file)


def extract_zip(zipfile="", path_from_local=""):
    filepath = path_from_local + zipfile
    extract_path = filepath.strip(".zip") + "/"
    parent_archive = ZipFile(filepath)
    parent_archive.extractall(extract_path)
    namelist = parent_archive.namelist()
    parent_archive.close()
    for name in namelist:
        try:
            if name[-4:] == ".zip":
                extract_zip(zipfile=name, path_from_local=extract_path)
        except:
            print("[!] Failed on", name)
            pass
    return extract_path


def download_bios(board_model):
    try:
        dl_path = f"/tmp/downloads/{board_model}/"
        latest_bios = get_lates_bios(board_model)
        if latest_bios is None:
            return
        mk_board_dir(dl_path)
        url, version = latest_bios
        print(f"[*] Found bios version {version} for board {board_model}")
        bios_zip = download_file(url, dl_path)

        # Extract
        print(f"[*] Extracting {bios_zip} ...")
        extract_zip(bios_zip, dl_path)

        # Locate and move
        bios_path = f"/tmp/supermicro/{board_model}/bios"
        print(f"[*] Moving the single BIOS file to {bios_path}")
        mk_board_dir(bios_path)
        biosfile = locate_and_move(dl_path, bios_path, BIOS_FILENAME_PATTERN)
        if biosfile:
            print(f"[*] The new bios is located at {biosfile}")
            return biosfile
        return None
    except Exception as err:
        print(err)
        return None


def download_bmc_firmware(board_model):
    try:
        dl_path = f"/tmp/downloads/{board_model}/"
        latest_bmc = get_lates_bmc_firmware(board_model)
        if latest_bmc is None:
            return
        mk_board_dir(dl_path)
        url, version = latest_bmc
        print(f"[*] Found BMC Firmware version {version} for board {board_model}")
        bmc_zip = download_file(url, dl_path)

        # Extract
        print(f"[*] Extracting {bmc_zip} ...")
        extract_zip(bmc_zip, dl_path)

        # Locate and move
        bmc_path = f"/tmp/supermicro/{board_model}/bmc"
        print(f"[*] Moving the single BMC Firmware file to {bmc_path}")
        mk_board_dir(bmc_path)
        bmcfile = locate_and_move(dl_path, bmc_path, BMC_FILENAME_PATTERN)
        if bmcfile:
            print(f"[*] The new bios is located at {bmcfile}")
            return bmcfile
        return None
    except Exception as err:
        print(err)
        return None


if __name__ == "__main__":
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    parser = argparse.ArgumentParser(
        description="Utility to download most recent BIOS & BMC Firmware from supermicro website"
    )
    parser.add_argument("-b", "--board", help="Motherboard Model")
    parser.add_argument("-f", "--file", help="TextFile containing a list of Boards")
    args = parser.parse_args()

    if args.board:
        board = args.board
        print(f"[*] Searching for latest BIOS for {board}")
        download_bios(board)
        print("*" * 50)
        print(f"[*] Searching for latest BMC Firmware for {board}")
        download_bmc_firmware(board)
        print("[*] Process finished!")
    elif args.file:
        filename = args.file
        try:
            if not os.path.isfile(filename):
                raise argparse.ArgumentTypeError(f"File {filename} does not exists.")
            with open(filename, "r") as f:
                num_files = 1
                for line in f:
                    board = line.strip()
                    print(
                        f"{num_files}: [*] Downloading BIOS and BMC Firmware for Board Model {board}"
                    )
                    download_bios(board)
                    download_bmc_firmware(board)
                    num_files += 1
        except Exception as e:
            print(e.args)
        else:
            print("Process finished sucessfull!")

    driver.close()
