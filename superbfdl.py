#!/usr/bin/env python3
import argparse
import os
import re
import shutil
from zipfile import ZipFile
from pathlib import Path

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
                bios_version = bios_version.lstrip('.').strip()
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
                bios_version = line.split(":")[1].replace("R", "").lstrip('.').strip()
                a = driver.find_element_by_partial_link_text(".zip")
                filename = a.text
                software_id = a.get_attribute("href").split("=")[-1]
                bios_dl_link = "https://www.supermicro.com/Bios/softfiles/{0}/{1}".format(
                    software_id, filename
                )

                if bios_version and bios_dl_link:
                    return (bios_dl_link, bios_version)
                else:
                    return (None, None)
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
        # print("[*] Download finished")
        return file_name
    else:
        return None


def write_version(output_dir, version):
    try:
        file_name = os.path.join(output_dir, "version.txt")
        with open(file_name, 'w') as vfile:
            vfile.writelines(version)
    except OSError as e:
        print("Error: %s" % e)


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
        except:  # noqa
            print("[!] Failed on", name)
            pass
    return extract_path


def download_bios(board_model, output_dir):
    try:
        dl_path = f"/tmp/downloads/{board_model}/"
        board_path = Path(f"{output_dir}/{board_model}")
        latest_bios = get_lates_bios(board_model)
        if latest_bios is None:
            return
        mk_board_dir(dl_path)
        url, version = latest_bios
        print(f"[*] Found bios version {version} for board {board_model}")

        print(f"[*] BIOS VERSION: {version}")
        bios_zip = download_file(url, dl_path)

        # Extract
        print(f"[*] Extracting {bios_zip} ...")
        extract_zip(bios_zip, dl_path)

        # Locate and move
        bios_path = os.path.join(board_path, "bios")
        if os.path.exists(bios_path):
            shutil.rmtree(bios_path)

        print(f"[*] Moving the single BIOS file to {bios_path}")
        mk_board_dir(bios_path)
        biosfile = locate_and_move(dl_path, bios_path, BIOS_FILENAME_PATTERN)
        if biosfile:
            print(f"[*] The new bios is located at {biosfile}")
            return (version, biosfile)
        return None
    except Exception as err:
        print(err)
        return None


def download_bmc_firmware(board_model, output_dir):
    try:
        dl_path = f"/tmp/downloads/{board_model}/"
        board_path = Path(f"{output_dir}/{board_model}")
        latest_bmc = get_lates_bmc_firmware(board_model)
        if latest_bmc is None:
            return
        mk_board_dir(dl_path)
        url, version = latest_bmc
        print(f"[*] Found BMC Firmware version {version} for board {board_model}")

        print(f"[*] BMC VERSION: {version}")
        bmc_zip = download_file(url, dl_path)

        # Extract
        print(f"[*] Extracting {bmc_zip} ...")
        extract_zip(bmc_zip, dl_path)

        # We only store one file version in the output dir
        bmc_path = os.path.join(board_path, "bmc")
        if os.path.exists(bmc_path):
            shutil.rmtree(bmc_path)

        print(f"[*] Moving the single BMC Firmware file to {bmc_path}")
        mk_board_dir(bmc_path)
        bmcfile = locate_and_move(dl_path, bmc_path, BMC_FILENAME_PATTERN)
        if bmcfile:
            print(f"[*] The new bios is located at {bmcfile}")
            return (version, bmcfile)
        return None
    except Exception as err:
        print(err)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Utility to download most recent BIOS & BMC Firmware from supermicro website"  # noqa
    )
    parser.add_argument("-b", "--board", help="Motherboard Model")
    parser.add_argument(
        "-f", "--file", help="TextFile containing a list of Boards")
    parser.add_argument(
        "-p", "--path", help="Path to where to save the downloaded bios/ipmi")  # noqa
    args = parser.parse_args()
    if not args.path:
        args.path = "."
    output_dir = Path(args.path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # browser object
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    if args.board:
        board = args.board
        print(f"[*] Searching for latest BIOS for {board}")
        bios = download_bios(board, output_dir)
        version_info = []
        if bios:
            bios_version, _ = bios
            version_info.append(f'BIOS={bios_version}\n')
        else:
            print("Could not find a BIOS version online.")
        print("*" * 50)
        print(f"[*] Searching for latest BMC Firmware for {board}")
        bmc = download_bmc_firmware(board, output_dir)
        if bmc:
            bmc_version, _ = bmc
            version_info.append(f'IPMI={bmc_version}\n')
        else:
            print("Could not find a BMC firmware online.")

        print("Writing version information ...")
        board_path = Path(f"{output_dir}/{board}")
        write_version(board_path, version_info)
    elif args.file:
        filename = args.file
        try:
            if not os.path.isfile(filename):
                raise argparse.ArgumentTypeError(f"File {filename} does not exists.")
            with open(filename, "r") as f:
                for num_files, line in enumerate(f):
                    board = line.strip()
                    print("Board #%s" % (num_files+1))
                    print("[*] Downloading BIOS and BMC Firmware for "
                          "Board Model %s" % board)
                    bios = download_bios(board, output_dir)
                    bmc = download_bmc_firmware(board, output_dir)
                    version_info = []
                    if bios:
                        bios_version, _ = bios
                        version_info.append(f'BIOS={bios_version}\n')
                    if bmc:
                        bmc_version, _ = bmc
                        version_info.append(f'IPMI={bmc_version}\n')
                    board_path = Path(f"{output_dir}/{board}")
                    write_version(board_path, version_info)
        except Exception as e:
            print(e)
        else:
            print("Process finished sucessfull!")
    driver.close()
