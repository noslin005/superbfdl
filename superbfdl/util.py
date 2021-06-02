import requests
import os
import shutil
import re
from zipfile import ZipFile
import sys

__author__ = "Nilson Lopes"

FW_NAME_PATTERN = {
    'ipmi': r"^[\w\-. ]+\.(bin|BIN)$",
    'bios': r"^[\w\-. ]+\.([A-Da-d]\d{2}|\d{3}|\d{3}_\w{3}|\w{3}_\w{3})$"
}


def download_file(url, dl_path):
    file_name = url.split("/")[-1].strip()
    print("[*] Downloading {0} to {1}".format(file_name, dl_path))
    resp = requests.get(url, stream=True)
    if resp.status_code == 200:
        file_path = os.path.join(dl_path, file_name)
        with open(file_path, "wb") as bfile:
            for chunk in resp.iter_content(chunk_size=1024):
                bfile.write(chunk)
        return file_name

    return None


def write_version(output_dir, version):
    try:
        file_name = os.path.join(output_dir, "version.txt")
        with open(file_name, 'w') as vfile:
            vfile.writelines(version)
    except OSError as e:
        print("Error: %s" % e)


def mkdir(path):
    """
    Make nested directory
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    except OSError as err:
        print(err.strerror)


def locate_and_move(dir_from, dir_to, fw_type):
    """
    Uses a regular expression to match bios or
    firmware files according to a pattern.
    The locate file in then moved to a given directory.
    """
    if fw_type not in ['bios', 'ipmi']:
        raise ValueError('fw_type should be "bios" or "ipmi", {} given'.format(
            type(fw_type)))

    pattern = FW_NAME_PATTERN.get(fw_type)
    for root, _dirs, files in os.walk(dir_from):
        for file in files:
            res = re.match(pattern, file)
            if res:
                filename = os.path.join(root, file)
                shutil.copy(filename, dir_to)
                return os.path.join(dir_to, file)


def extract_zip(zipfile="", path_from_local=""):
    """
    Extract a zip file recursively
    """
    filepath = path_from_local + zipfile
    extract_path = filepath.strip(".zip") + "/"
    parent_archive = ZipFile(filepath)
    parent_archive.extractall(extract_path)
    namelist = parent_archive.namelist()
    parent_archive.close()
    for name in namelist:
        try:
            # dont extract sum utility
            if name.lower().startswith('sum'):
                continue
            if name[-4:] == ".zip":
                extract_zip(zipfile=name, path_from_local=extract_path)

        except Exception as e:  # noqa
            sys.stderr.write(f'Error while extracting {name}\n')
            pass
    return extract_path


def download_extract(file):
    pass
