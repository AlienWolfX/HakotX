import os
import csv
import xml.etree.ElementTree as ET
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import configparser

load_dotenv()

username = os.getenv("HOME_USERNAME")
password = os.getenv("HOME_PASSWORD")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load config properties
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', '.config.properties'))

HOME_XML_FOLDER = config.get('folders', 'home_xml_folder', fallback='./home_xml')
CSV_FOLDER = config.get('folders', 'csv_folder', fallback='./csv')

def send_login_request(ip):
    url = f"http://{ip}/boaform/admin/formLogin"
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"username": username, "psd": password}

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        logging.info(f"Login request sent successfully to {ip}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send login request to {ip}: {str(e)}")
        raise

def send_download_request(ip):
    url = f"http://{ip}/boaform/formSaveConfig"
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"save_cs": "Backup..."}

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        filename = f"{ip}.xml"
        os.makedirs(HOME_XML_FOLDER, exist_ok=True)
        file_path = os.path.join(HOME_XML_FOLDER, filename)
        with open(file_path, "wb") as file:
            file.write(response.content)
        logging.info(f"Downloaded file saved: {file_path}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download config from {ip}: {str(e)}")
        raise

def process_ip(ip):
    """Process an IP address by sending login and download requests."""
    try:
        send_login_request(ip)
        send_download_request(ip)
        return ip
    except requests.exceptions.RequestException:
        return None

def read_ip_files():
    """Read IPs from both SPU-GE120W-H.txt and ONU4FER1TVASWB.txt files."""
    ip_list = []
    files_to_read = ["./ips/SPU-GE120W-H.txt", "./ips/ONU4FER1TVASWB.txt"]
    
    for file_path in files_to_read:
        try:
            with open(file_path, "r") as file:
                ips = file.read().splitlines()
                ip_list.extend(ips)
                logging.info(f"Read {len(ips)} IPs from {file_path}")
        except FileNotFoundError:
            logging.warning(f"File not found: {file_path}")
        except Exception as e:
            logging.error(f"Error reading {file_path}: {str(e)}")
    
    # Remove duplicates while preserving order
    unique_ips = list(dict.fromkeys(ip_list))
    logging.info(f"Total unique IPs to process: {len(unique_ips)}")
    return unique_ips

def main():
    ip_list = read_ip_files()
    
    if not ip_list:
        logging.error("No IPs found to process")
        return []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_ip, ip): ip for ip in ip_list}
        completed_ips = []
        for future in as_completed(futures):
            result = future.result()
            if result:
                completed_ips.append(result)

    logging.info(f"Successfully processed {len(completed_ips)} IPs")
    return completed_ips

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
            ip = filename[:-4]
            file_path = os.path.join(directory, filename)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                mac_element = root.find(".//Value[@Name='MacAddr']")
                ssid_element = root.find(".//Value[@Name='SSID']")
                keypassphrase_element = root.find(".//Value[@Name='WSC_PSK']")

                if mac_element is not None and ssid_element is not None and keypassphrase_element is not None:
                    mac = normalize_mac(mac_element.attrib["Value"])
                    ssid = ssid_element.attrib["Value"]
                    keypassphrase = keypassphrase_element.attrib["Value"]
                    ssid_key_pairs.append((ip, mac, ssid, keypassphrase))
            except ET.ParseError as e:
                logging.error(f"Error parsing XML file {file_path}: {str(e)}")

    return ssid_key_pairs

def save_to_csv(pairs, output_file):
    # Sort pairs by IP address
    sorted_pairs = sorted(pairs, key=lambda x: x[0])
    
    # Ensure the CSV output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "MAC", "SSID_2G", "PSK_2G"])
        writer.writerows(sorted_pairs)
    logging.info(f"Data written to CSV file {output_file}")

if __name__ == "__main__":
    try:
        completed_ips = main()
        directory_path = HOME_XML_FOLDER
        output_file = os.path.join(CSV_FOLDER, "spu_ge120w+onu4fer1tvaswb.csv")

        pairs = parse_xml_files(directory_path)
        save_to_csv(pairs, output_file)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")