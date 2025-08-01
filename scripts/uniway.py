import os
import requests
import re
import csv
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from dotenv import load_dotenv
import configparser

load_dotenv()

username = os.getenv("UNIWAY_USERNAME")
password = os.getenv("UNIWAY_PASSWORD")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load config properties
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', '.config.properties'))

UNIWAY_XML_FOLDER = config.get('folders', 'uniway_xml_folder', fallback='./uniway_xml')
CSV_FOLDER = config.get('folders', 'csv_folder', fallback='./csv')

def send_login_request(ip, code, csrf):
    try:
        link = f"http://{ip}/boaform/admin/formLogin"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": f"http://{ip}",
            "Connection": "keep-alive",
            "Referer": f"http://{ip}/admin/login.asp",
        }
        data = {
            "username1": username,
            "psd1": password,
            "verification_code": code,
            "username": username,
            "psd": password,
            "csrftoken": csrf,
        }

        resp = requests.post(link, headers=headers, data=data)
        resp.raise_for_status()
        logging.info(f"Login request sent successfully to {ip}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send login request to {ip}: {e}")
        raise

def download_request(ip, csrf):
    try:
        link = f"http://{ip}/boaform/admin/formMgmConfig"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": f"http://{ip}",
            "Connection": "keep-alive",
            "Referer": f"http://{ip}/mgm_config_file.asp",
        }

        data = {"action": "saveconfigfile", "submit-url": "", "csrftoken": csrf}

        resp = requests.post(link, headers=headers, data=data)
        resp.raise_for_status()
        
        filename = f"{ip}.xml"
        os.makedirs(UNIWAY_XML_FOLDER, exist_ok=True)
        file_path = os.path.join(UNIWAY_XML_FOLDER, filename)
        with open(file_path, "wb") as config:
            config.write(resp.content)
        logging.info(f"Downloaded file saved: {file_path}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send download request to {ip}: {e}")
        raise

def normalize_mac(mac):
    """Normalize MAC address to uppercase with colons."""
    mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
    if len(mac) >= 12:
        mac = mac[:12] 
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    return mac

def parse_xml_files(directory):
    """Parses XML files in the specified directory and extracts SSID and KeyPassphrase pairs."""
    ssid_key_pairs = []

    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            ip = filename.replace(".xml", "")
            file_path = os.path.join(directory, filename)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                mac_element = root.find(".//Value[@Name='macAddr']")
                ssid_element = root.find(".//Value[@Name='SSID']")
                keypassphrase_element = root.find(".//Value[@Name='WSC_PSK']")

                if mac_element is not None and ssid_element is not None and keypassphrase_element is not None:
                    mac = normalize_mac(mac_element.attrib["Value"])
                    ssid = ssid_element.attrib["Value"]
                    keypassphrase = keypassphrase_element.attrib["Value"]

                    ssid_key_pairs.append((ip, mac, ssid, keypassphrase))
            except ET.ParseError as e:
                logging.error(f"Failed to parse XML file: {file_path} - {e}")

    return ssid_key_pairs

def save_to_csv(pairs, output_file):
    sorted_pairs = sorted(pairs, key=lambda x: x[0])
    # Ensure the CSV output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "MAC", "SSID_2G", "PSK_2G"])
        writer.writerows(sorted_pairs)

def main():
    with open("./ips/uniway.txt", "r") as file:
        ip_list = [ip.strip() for ip in file.readlines()]

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {}
        for ip in ip_list:
            future = executor.submit(process_ip, ip)
            future_to_ip[future] = ip

        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                future.result()
            except Exception as e:
                logging.error(f"Failed to process {ip}: {e}")

def process_ip(ip):
    try:
        url = f"http://{ip}"
        response = requests.get(url)
        response.raise_for_status()

        check_code_match = re.search(
            r"document\.getElementById\('check_code'\)\.value='([^']*)';", response.text
        )
        check_code_value = check_code_match.group(1) if check_code_match else None
        csrf_token_match = re.search(
            r"<input type='hidden' name='csrftoken' value='([^']*)' />", response.text
        )
        csrf_token_value = csrf_token_match.group(1) if csrf_token_match else None

        if check_code_value and csrf_token_value:
            send_login_request(ip, check_code_value, csrf_token_value)
            download_request(ip, csrf_token_value)
        else:
            logging.warning(f"Failed to find check_code or csrftoken for {ip}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to process {ip}: {e}")
        raise

if __name__ == "__main__":
    main()
    directory_path = UNIWAY_XML_FOLDER
    output_file = os.path.join(CSV_FOLDER, "uniway.csv")
    pairs = parse_xml_files(directory_path)
    save_to_csv(pairs, output_file)
