
#!/bin/sh
if [ "$(id -u)" -ne 0 ]; then
    echo 'This script must be run by root' >&2
    exit 1
fi
apt-get update
apt-get install -y firefox python3 python3-pip
pip3 install selenium
pip3 install requests
wget https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz -O /tmp/geckodriver.tar.gz
tar -C /opt -xzf /tmp/geckodriver.tar.gz
chmod 755 /opt/geckodriver
ln -fs /opt/geckodriver /usr/bin/geckodriver
cp ./superbfdl.py /usr/local/bin/superbfdl
chmod 755 /usr/local/bin/superbfdl
