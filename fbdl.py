#!/usr/bin/env python3
"""
1. Contruct the link to get the motherboard details
2. Get the ProductID and ProductName from the hiden input form field
3. Construct the payload
4. send a post request to the 'results.aspx' (BIOS) or 'firmware.aspx'(IPMI)
 page
5. parse the html text and retrive the BIOS/IPMI information Revision and
SoftwareID
6. Build and return the download link
"""
import requests
from bs4 import BeautifulSoup
import os
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

SUPERMICRO_URL = "https://www.supermicro.com"

FW_ENDPOINT = {
    'ipmi': "support/bios/firmware.aspx",
    'bios': "support/resources/results.aspx"
}


def get_product_info(board_model):
    """
    Parses the motherboard html page and retrieve the
    ProductID and the ProductName
    """
    url = f"{SUPERMICRO_URL}/en/products/motherboard/{board_model}"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    product_id = soup.find('input', {'name': 'ProductID'}).get('value')
    return product_id


def get_fw_information(product_id, product_name, fw_type):
    """
    Submit a post request to the bios resource website and retrieve
    the information about the latest bios.
    The information returned includes the download link to be used
    to download the bios file
    """
    if fw_type not in ['bios', 'ipmi']:
        raise ValueError('fw_type should be "bios" or "ipmi", {} given'.format(
            type(fw_type)))

    url = f"{SUPERMICRO_URL}/{FW_ENDPOINT[fw_type]}"
    log.info(url)

    payload = {
        "ProductID": product_id,
        "ProductName": product_name,
        "Resource": "BIOS"
    }
    page = requests.post(url, data=payload)

    soup = BeautifulSoup(page.text, 'html.parser')

    results = {}
    for row in soup.find_all('tr', {"class": "textA"}):
        columns = row.findAll('td')
        key_name = columns[0].text.strip().replace(':', '')
        results[key_name] = columns[1].text.strip()
        link = columns[1].find('a')
        if link:
            file_name = link.text
            href = link.attrs['href']
            if href.startswith('/about'):
                software_id = href.split("=")[-1]
                results['download_url'] = (f"{SUPERMICRO_URL}/Bios/softfiles/"
                                           f"{software_id}/{file_name}")
    return results


def download(url, dl_path):
    file_name = url.split("/")[-1].strip()
    log.info(f"Downloading {file_name} to {dl_path}")
    resp = requests.get(url, stream=True)
    if resp.status_code == 200:
        file_path = os.path.join(dl_path, file_name)
        with open(file_path, "wb") as bfile:
            for chunk in resp.iter_content(chunk_size=1024):
                bfile.write(chunk)
        return file_name


if __name__ == "__main__":
    board = "X11DPU"
    output_dir = "/tmp"
    log.info("Getting the Motherboard ProductID ...")
    product_id = get_product_info(board)

    log.info("Retrieving the latest BIOS from supermicro ...")
    bios_info = get_fw_information(product_id, board, fw_type="bios")
    bios_url = bios_info.get('download_url')
    print(bios_info)
    log.info("Download BIOS ...")
    download(bios_url, output_dir)

    log.info("Retrieving the latest IPMI from supermicro ...")
    bmc_info = get_fw_information(product_id, board, fw_type="ipmi")
    bmc_url = bmc_info.get('download_url')
    log.info("Download IPMI ...")
    download(bmc_url, output_dir)
    print(bmc_info)
