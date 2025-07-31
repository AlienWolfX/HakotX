import os
import subprocess
import re
import csv
import xml.etree.ElementTree as ET
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import configparser

load_dotenv()

username = os.getenv("REALTEK_USERNAME")
password = os.getenv("REALTEK_PASSWORD")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load config properties
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', '.config.properties'))

REALTEK_XML_FOLDER = config.get('folders', 'realtek_xml_folder', fallback='./realtek_xml')
CSV_FOLDER = config.get('folders', 'csv_folder', fallback='./csv')

def send_login_request(ip):
    try:
        if download_config(ip, ""):
            return True
            
        response = requests.get(f"http://{ip}", timeout=4)
        check_code = re.search(r"document\.getElementById\('check_code'\)\.value='([^']*)';", response.text)
        csrf_token = re.search(r"<input type='hidden' name='csrftoken' value='([^']*)' />", response.text)
        
        if not check_code or not csrf_token:
            logging.warning(f"Could not find tokens for {ip}, trying download anyway")
            return True
            
        login_command = [
            "curl",
            f"http://{ip}/boaform/admin/formLogin",
            "-H", "Content-Type: application/x-www-form-urlencoded",
            "-H", f"Origin: http://{ip}",
            "-H", "Connection: keep-alive", 
            "-H", f"Referer: http://{ip}/admin/login.asp",
            "--data-raw", f"challenge=&username={username}&password={password}&verification_code={check_code.group(1)}&save=Login&submit-url=%2Fadmin%2Flogin.asp&csrftoken={csrf_token.group(1)}",
            "--insecure"
        ]
        subprocess.run(login_command, capture_output=True, text=True)
        return True

    except Exception as e:
        logging.error(f"Error in login process for {ip}: {str(e)}")
        return False

def download_config(ip, csrf):
    download_command = [
        "curl",
        f"http://{ip}/boaform/formSaveConfig",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-H", f"Origin: http://{ip}",
        "-H", "Connection: keep-alive",
        "-H", f"Referer: http://{ip}/saveconf.asp",
        "--data-raw", f"save_cs=Backup+as+file&csrftoken={csrf}",
        "--insecure",
        "-o", os.path.join(REALTEK_XML_FOLDER, f"{ip}.xml")
    ]
    try:
        result = subprocess.run(download_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Download failed: {result.stderr}")
        return True
    except Exception as e:
        logging.error(f"Error downloading config from {ip}")
        return False

def normalize_mac(mac):
    """Normalize MAC address to uppercase with colons."""
    mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
    if len(mac) >= 12:
        mac = mac[:12] 
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    return mac

def parse_xml_files(directory):
    ssid_key_pairs = []

    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            file_path = os.path.join(directory, filename)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                mac_element = root.find(".//Value[@Name='MacAddr']")
                ssid_element = root.find(".//Value[@Name='ssid']")
                keypassphrase_element = root.find(".//Value[@Name='WLAN_WPA_PSK']")

                if mac_element is not None and ssid_element is not None and keypassphrase_element is not None:
                    mac_normalized = normalize_mac(mac_element.attrib.get("Value", ""))
                    ssid = ssid_element.attrib.get("Value", "")
                    keypassphrase = keypassphrase_element.attrib.get("Value", "")
                    ip = filename.replace(".xml", "")
                    ssid_key_pairs.append((ip, mac_normalized, ssid, keypassphrase))
            except ET.ParseError as e:
                logging.error(f"Error parsing XML file {file_path}: {e}")

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
    failed_operations = []
    os.makedirs(REALTEK_XML_FOLDER, exist_ok=True)
    
    try:
        with open("./ips/realtek.txt", "r") as file:
            ip_list = [ip.strip() for ip in file.readlines()]
    except FileNotFoundError:
        logging.error("realtek.txt not found")
        return

    with ThreadPoolExecutor(max_workers=5) as executor:
        for ip in ip_list:
            try:
                csrf = send_login_request(ip)
                if csrf:
                    if download_config(ip, csrf):
                        logging.info(f"Successfully processed {ip}")
                    else:
                        failed_operations.append(f"{ip} (config download failed)")
                else:
                    failed_operations.append(f"{ip} (login failed)")
            except Exception as e:
                logging.error(f"Error processing {ip}: {str(e)}")
                failed_operations.append(ip)
    
    if failed_operations:
        logging.info("Failed operations:")
        for ip in failed_operations:
            logging.info(f"- {ip}")
    else:
        logging.info("XML download is successful")
        
    logging.info("Now parsing XML files")
    
    pairs = parse_xml_files(REALTEK_XML_FOLDER)
    save_to_csv(pairs, os.path.join(CSV_FOLDER, "realtek_pass.csv"))
    
    logging.info("All Done")

if __name__ == "__main__":
    main()