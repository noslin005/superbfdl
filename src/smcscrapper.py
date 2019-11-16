from selenium.webdriver import Firefox
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options

BOARD_URL = "https://www.supermicro.com/en/products/motherboard"
DOWNLOAD_URL = "https://www.supermicro.com/Bios/softfiles"


class Supermicro:
    def __init__(self):
        # # Create a headless browser
        opts = Options()
        opts.set_headless()
        self.browser = Firefox(options=opts)
        self.firmwares = {}

    def get_firmware(self, board_model, firmware_type):
        page_keywords = {
            "bios": {
                "form": "javascript:document.biosForm.submit();",  # noqa
                "text": "BIOS Revision",
            },
            "bmc": {
                "form": "javascript:document.IPMIForm.submit();",
                "text": "Firmware Revision",
            },
        }
        if not firmware_type in page_keywords:
            return False
        form = page_keywords[firmware_type].get("form")
        text = page_keywords[firmware_type].get("text")
        url = f"{BOARD_URL}/{board_model}"
        try:
            self.browser.get(url)
            self.browser.find_element_by_xpath('//a[@href="{0}"]'.format(form)).click()
            raw = self.browser.find_element_by_class_name("yui-skin-sam").text
            raw = raw.split("\n")
            for line in raw:
                if text in line:
                    version = line.split(":")[1].replace("R", "").strip()
                    a = self.browser.find_element_by_partial_link_text(".zip")
                    filename = a.text
                    software_id = a.get_attribute("href").split("=")[-1]
                    dl_link = f"{DOWNLOAD_URL}/{software_id}/{filename}"
                    if version and dl_link:
                        tmp = {}
                        tmp[firmware_type] = {
                            "version": version,
                            "link": dl_link,
                        }
                        self.firmwares[board_model] = tmp
                        return True
            return False
        except (Exception, NoSuchElementException) as err:
            print(err.msg)
            return False

    def get_bios(self, board_model):
        firmware_type = "bios"
        check_bios = self.get_firmware(board_model, firmware_type)
        if check_bios:
            bios = self.firmwares[board_model].get(firmware_type)
            return bios
        return None

    def get_bmc(self, board_model):
        firmware_type = "bmc"
        check_bmc = self.get_firmware(board_model, firmware_type)
        if check_bmc:
            bmc = self.firmwares[board_model].get(firmware_type)
            return bmc
        return None

    def close(self):
        self.browser.quit()
