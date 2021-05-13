#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
import sys

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

SUPERMICRO_URL = "https://www.supermicro.com"

FW_ENDPOINT = {
    'ipmi': "support/bios/firmware.aspx",
    'bios': "support/resources/results.aspx"
}


def query_product_id(board_model):
    """
    Parses the motherboard html page and retrieve
    the ProductID
    """
    print(f'[*] Querying for ProductID matching board {board_model}')

    url = f"{SUPERMICRO_URL}/en/products/motherboard/{board_model}"
    try:
        page = requests.get(url)
        if page.status_code != 200:
            raise ValueError(f"Get wrong response from {url}")
        soup = BeautifulSoup(page.text, 'html.parser')
        product_id = soup.find('input', {'name': 'ProductID'}).get('value')

    except Exception as e:
        log.debug(e)
        log.error(f"Could not find Product ID for {board_model} ")
        return
    return product_id


def get_board_info(board_model, product_id, fw_type):
    """
    Submit a post request to the bios resource website and retrieve
    the information about the latest bios.
    The information returned includes the download link to be used
    to get the bios file.
    """
    if fw_type not in ['bios', 'ipmi']:
        raise ValueError('fw_type should be "bios" or "ipmi", {} given'.format(
            type(fw_type)))

    url = f"{SUPERMICRO_URL}/{FW_ENDPOINT[fw_type]}"

    payload = {
        "ProductID": product_id,
        "ProductName": board_model,
        "Resource": "BIOS"
    }

    page = requests.post(url, data=payload)

    soup = BeautifulSoup(page.text, 'html.parser')

    regex = re.compile(r"[Ss]oftware[Ii]tem[Ii][DD]=(?P<pid>\d*)")

    results = {}

    results['download_url'] = ''

    for row in soup.find_all('tr', {"class": "textA"}):
        columns = row.findAll('td')
        key_name = columns[0].text.replace(':', '').strip()
        results[key_name] = columns[1].text.strip()
        a_link = columns[1].find('a')
        if a_link:
            file_name = a_link.text
            href = a_link.attrs['href']
            # href: /about/policies/disclaimer.cfm?SoftwareItemID=12558
            match = regex.search(href)
            if match and file_name.endswith('zip'):
                software_id = match['pid']
                results['download_url'] = (f"{SUPERMICRO_URL}/Bios/softfiles/"
                                           f"{software_id}/{file_name}")
    print(results)

    data = {}
    data[fw_type] = {}
    for key, value in results.items():
        if "BIOS Revision" in key:
            bios_version = value.replace("R", "").lstrip('.').strip()
            data['bios_revision'] = bios_version
            data[fw_type]['release'] = bios_version
            print(f"[*] Found BIOS Revision: {bios_version}")

        # some boards show IPMI Firmware Revision
        if 'Firmware Revision' in key:
            ipmi_revision = value.replace("R", "").lstrip('.').strip()
            data['ipmi_revision'] = ipmi_revision
            data[fw_type]['release'] = ipmi_revision
            print(f"[*] Found IPMI Firmware Revision: {ipmi_revision}")

        if 'Bundled Software' in key:
            data['bundle'] = True

        if 'Firmware Release Note' in key:
            data['ipmi_release_note'] = value

    data['ipmi_version'] = results.get('IPMI Firmware Revision')
    data['download_url'] = results['download_url']
    data['product_id'] = product_id
    data['board_model'] = board_model

    # some board (X11DPU) does not display ipmi firmware release
    # we can retrieve this information from the release note file
    # i.e. X11DPU_BMCFW_1_73_06_release_notes.pdf has release info
    # 1.73.06
    if data.get('bundle') is True and not data.get('ipmi_revision'):
        if not data.get('ipmi_revision'):
            release_note = data['ipmi_release_note']
            release_parts = [d for d in release_note.split('_') if d.isdigit()]
            ipmi_revision = '.'.join(release_parts)
            data['ipmi_revision'] = ipmi_revision
            data[fw_type]['release'] = ipmi_revision
            print(f"[*] Found IPMI Firmware Revision: {ipmi_revision}")

    print(data)
    return data
