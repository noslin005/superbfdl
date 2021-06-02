#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

SUPERMICRO_URL = "https://www.supermicro.com"

IPMI_URL_RESOURCE = f"{SUPERMICRO_URL}/support/bios/firmware.aspx"
BIOS_URL_RESOURCE = f"{SUPERMICRO_URL}/support/resources/results.aspx"


class SMC(object):
    def __init__(self, board_model):
        self.board_model = board_model
        self.product_id = 0x0
        self.ipmi_revision = None
        self.bios_revision = None
        self.ipmi_url = None
        self.bios_url = None
        self.software_id = None

    def __repr__(self) -> str:
        return (f"Board: {self.board_model} ({self.product_id}), "
                f"BIOS: {self.bios_revision}, "
                f"IPMI: {self.ipmi_revision}")

    def get_board_product_id(self):
        """
        Parses the motherboard html page and retrieve
        the ProductID.

        The url https://www.supermicro.com/en/products/motherboard/<BOARD>
        ha the following hidden form elements:

        <form name="biosForm" method="post"
            action="/support/resources/results.aspx">
            <input type="hidden" name="ProductID" value="85553">
            <input type="hidden" name="Resource" value="BIOS">
            <input type="Hidden" name="ProductName" value="X11DPU">
            <a href="javascript:document.biosForm.submit();">
            Update Your BIOS</a>
        </form>

        The action attribute will vary, depending if it's bios on ipmi:
        BIOS: action="/support/resources/results.aspx"
        IPMI: action="/support/bios/firmware.aspx"
        """
        url = f"{SUPERMICRO_URL}/en/products/motherboard/{self.board_model}"
        try:
            page = requests.get(url)
            if page.status_code != 200:
                raise ValueError(f"Get wrong response from {url}")
            soup = BeautifulSoup(page.text, 'html.parser')
            product_id = soup.find('input', {'name': 'ProductID'}).get('value')
        except Exception as e:
            log.debug(e)
            log.error(f"Could not find Product ID for {self.board_model} ")
            return
        self.product_id = product_id
        return product_id

    def sanitize_data(self, resources):
        """
        This will receive the dictionary containing the key:val
        pairs from build_download_url, and will make it readable.

        From:
        {
            "Bundled Software File Name" : "X11DPU3_4_AST173_06.zip
            "Size (KB)" : "75,401"
            "BIOS Revision" : "3.4"
            "BIOS Release Note" : "X11DPU_BIOS_3_4_release_notes.pdf"
            "IPMI Firmware Release Note" : "X11DPU_BMCFW_1_73_06_release...pdf"
            "File Description" : "...",
            "bundle": True,
            "download_url": "https://www.supermicro.com/Bios/softfiles/
                            12612/X11DPU3_4_AST173_06.zip"
        }

        To:
        {
            'bios': {
                'revision': '3.2',
                'url': 'https://www.supermicro.com/Bios/softfiles/10581/
                        X10DRW9_B22.zip'
                }
        }
        """
        data = {}
        data['bundle'] = False
        ipmi_release_note = ""

        for key, value in resources.items():
            if "Bundled Software" in key:
                data['bundle'] = True

            if "BIOS Revision" in key:
                data['bios'] = {}
                bios_version = value.replace("R", "").lstrip('.').strip()
                data['bios']['revision'] = bios_version
                data['bios']['url'] = resources['download_url']

            # Some boards show 'IPMI Firmware Revision' and others just
            # 'Firmware Revision'
            if 'Firmware Revision' in key:
                data['ipmi'] = {}
                ipmi_revision = value.replace("R", "").lstrip('.').strip()
                data['ipmi']['revision'] = ipmi_revision
                data['ipmi']['url'] = resources['download_url']

            # save this for the line below
            if 'Firmware Release Note' in key:
                ipmi_release_note = value

        # Some pages (X11DPU) does not shows the 'IPMI Firmware Revision' line.
        # This is a hack to get the information from the release note filename,
        # i.e. X11DPU_BMCFW_1_73_06_release_notes.pdf shows 1.73.06

        if data.get('bundle'):
            try:
                data['ipmi'].get('revision')
            except KeyError:
                release_parts = [
                    d for d in ipmi_release_note.split('_') if d.isdigit()
                ]
                ipmi_revision = '.'.join(release_parts)
                data['ipmi'] = {}
                data['ipmi']['revision'] = ipmi_revision
                data['ipmi']['url'] = resources['download_url']

        return data

    def build_download_url(self, resource_url):
        """
        Build the download url
        """
        payload = {
            "ProductID": self.product_id,
            "ProductName": self.board_model,
            "Resource": "BIOS"
        }

        page = requests.post(resource_url, data=payload)
        soup = BeautifulSoup(page.text, 'html.parser')
        regex = re.compile(r"[Ss]oftware[Ii]tem[Ii][Dd]=(?P<pid>\d*)")

        resources = {}

        for row in soup.find_all('tr', {"class": "textA"}):
            columns = row.findAll('td')
            # Bundled Software File Name: X11DPU3_4_AST173_06.zip
            # <a href=/about/policies/disclaimer.cfm?SoftwareItemID=12612>.</a>
            # Size (KB): 75,401
            # BIOS Revision: 3.4
            # BIOS Release Note: X11DPU_BIOS_3_4_release_notes.pdf
            # IPMI Firmware Release Note: X11DPU_BMCFW_1_73_06_release...pdf
            # File Description: ...
            key_name = columns[0].text.replace(':', '').strip()
            resources[key_name] = columns[1].text.strip()
            a_link = columns[1].find('a')

            if a_link:
                # receice 'X11DPU3_4_AST173_06.zip'
                file_name = a_link.text
                # receive '/about/policies/disclaimer.cfm?SoftwareItemID=12612'
                href = a_link.attrs['href']
                # extract the numeric part of SoftwareItemID=12612, i.e. 12612
                match = regex.search(href)
                # we don't want the pdf files, just the zip
                if match and file_name.endswith('zip'):
                    software_id = match['pid']

                    self.software_id = software_id
                    # # builds a direct link to download the firmware
                    # # https://supermicro.com/Bios/softfiles/12612/
                    # # X11DPU3_4_AST173_06.zip
                    resources['download_url'] = (
                        f"{SUPERMICRO_URL}/Bios/softfiles/"
                        f"{software_id}/{file_name}")
        # print(resources)
        return self.sanitize_data(resources)

    def get_bios_info(self):
        resources = self.build_download_url(BIOS_URL_RESOURCE)
        try:
            self.bios_url = resources['bios'].get('url')
            self.bios_revision = resources['bios'].get('revision')
        except (KeyError, IndexError):
            pass

    def get_ipmi_info(self):
        resources = self.build_download_url(IPMI_URL_RESOURCE)
        try:
            self.ipmi_url = resources['ipmi'].get('url')
            self.ipmi_revision = resources['ipmi'].get('revision')
        except (KeyError, IndexError):
            pass

    def get_firmwares(self):
        self.get_bios_info()
        self.get_ipmi_info()


if __name__ == "__main__":
    # smc = SMC('X11DPU')
    smc = SMC('H11DSi-NT')
    smc.get_board_product_id()
    smc.get_firmwares()
    print(smc)
