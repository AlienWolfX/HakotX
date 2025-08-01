import os
import requests
import csv
import xml.etree.ElementTree as ET
import logging
from dotenv import load_dotenv
import configparser
import time

load_dotenv()

username = os.getenv("BOA_USERNAME")
password = os.getenv("BOA_PASSWORD")

logging.basicConfig(level=logging.INFO)

# Load config properties
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', '.config.properties'))

BOA_XML_FOLDER = config.get('folders', 'boa_xml_folder', fallback='./xpn_rh2_00-07_xml')
CSV_FOLDER = config.get('folders', 'csv_folder', fallback='./csv')


def send_login_request(session, ip):
    """Sends a login request to the specified IP address."""
    url = f"http://{ip}/boaform/webLogin"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": f"http://{ip}",
        "Connection": "keep-alive",
        "Referer": f"http://{ip}/login.asp",
    }
    data = {"username": username, "password": password}

    response = session.post(url, headers=headers, data=data)
    response.raise_for_status() 
    logging.info(f"Login request sent successfully to {ip}")


def send_download_request(session, ip):
    """Sends a download request to the specified IP address."""
    url = f"http://{ip}/boaform/settingConfig"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"http://{ip}",
        "Connection": "keep-alive",
        "Referer": f"http://{ip}/page/config.asp?0",
        "Upgrade-Insecure-Requests": "1",
    }
    data = {"config_backup": "Backup"}

    response = session.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raise an exception if the request fails

    filename = f"{ip}.xml"
    os.makedirs(BOA_XML_FOLDER, exist_ok=True)
    file_path = os.path.join(BOA_XML_FOLDER, filename)
    with open(file_path, "wb") as file:
        file.write(response.content)
    logging.info(f"Downloaded file saved: {file_path}")


def main():
    """Main function that sends login and download requests to a list of IP addresses."""
    with requests.Session() as session:
        with open("./ips/XPN_RH2_00-07.txt", "r") as file:
            ip_list = file.read().splitlines()

        for ip in ip_list:
            try:
                send_login_request(session, ip)
                time.sleep(0.5)
                send_download_request(session, ip)
            except requests.RequestException as e:
                logging.error(f"Failed to send requests to {ip}: {str(e)}")

def normalize_mac(mac):
    """Normalize MAC address to uppercase with colons."""
    mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
    if len(mac) >= 12:
        mac = mac[:12] 
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    return mac

def parse_xml_files(directory):
    """Parses XML files in a directory and returns a list of (IP, SSID, KeyPassphrase, MAC Address) tuples."""
    ssid_key_pairs = []

    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            file_path = os.path.join(directory, filename)
            ip = filename[:-4]
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                ssid_element = root.find(".//Value[@Name='SSID']")
                keypassphrase_element = root.find(".//Value[@Name='WSC_PSK']")
                mac_element = root.find(".//Value[@Name='macAddr']") 

                if mac_element is not None and ssid_element is not None and keypassphrase_element is not None:
                    ssid = ssid_element.attrib["Value"]
                    keypassphrase = keypassphrase_element.attrib["Value"]
                    mac = normalize_mac(mac_element.attrib["Value"])

                    ssid_key_pairs.append((ip, mac, ssid, keypassphrase))
            except ET.ParseError as e:
                logging.error(f"Error parsing XML file {file_path}: {str(e)}")

    return ssid_key_pairs


def save_to_csv(pairs, output_file):
    sorted_pairs = sorted(pairs, key=lambda x: x[0])
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "MAC", "SSID", "KeyPassphrase"])
        writer.writerows(sorted_pairs)


if __name__ == "__main__":
    try:
        main()
        directory_path = BOA_XML_FOLDER
        output_file = os.path.join(CSV_FOLDER, "xpn_rh2_00-07.csv")

        pairs = parse_xml_files(directory_path)

        save_to_csv(pairs, output_file)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")