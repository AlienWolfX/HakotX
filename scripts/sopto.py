import subprocess
import logging
import csv
import xml.etree.ElementTree as ET
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("SOPTO_USERNAME")
password = os.getenv("SOPTO_PASSWORD")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

XML_DIRECTORY = "./sopto_xml"
COOKIE_DIRECTORY = "cookies"

def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [XML_DIRECTORY, COOKIE_DIRECTORY]
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Directory {directory} is ready")
        except Exception as e:
            logging.error(f"Failed to create directory {directory}: {str(e)}")
            raise

def send_login_request(ip):
    login_command = [
        'curl',
        f'http://{ip}/boaform/admin/formLogin',
        '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        '-H', 'Accept-Language: en-US,en',
        '-H', 'Cache-Control: max-age=0',
        '-H', 'Connection: keep-alive',
        '-H', 'Content-Type: application/x-www-form-urlencoded',
        '-H', 'Cookie: userLanguage=en',
        '-H', f'Origin: http://{ip}',
        '-H', f'Referer: http://{ip}/admin/login.asp',
        '-H', 'Sec-GPC: 1',
        '-H', 'Upgrade-Insecure-Requests: 1',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
        '--data-raw', f'challenge=&username={username}&password={password}&save=Login&submit-url=%2Fadmin%2Flogin.asp&postSecurityFlag=12726',
        '--insecure',
    ]
    try:
        result = subprocess.run(login_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Login failed: {result.stderr}")
        return True
    except Exception as e:
        logging.error(f"Error logging in to {ip}: {str(e)}")
        return False

def download_config(ip):
    download_command = [
        'curl',
        f'http://{ip}/boaform/formSaveConfig',
        '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        '-H', 'Accept-Language: en-US,en',
        '-H', 'Cache-Control: max-age=0',
        '-H', 'Connection: keep-alive',
        '-H', 'Content-Type: application/x-www-form-urlencoded',
        '-b', os.path.join(COOKIE_DIRECTORY, f'{ip}_cookies.txt'),  # Updated cookie path
        '-H', f'Origin: http://{ip}',
        '-H', f'Referer: http://{ip}/saveconf.asp',
        '-H', 'Sec-GPC: 1',
        '-H', 'Upgrade-Insecure-Requests: 1',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
        '--data-raw', 'save_cs=Backup...&submit-url=%2Fsaveconf.asp&postSecurityFlag=63991',
        '--insecure',
        '-o',
        os.path.join(XML_DIRECTORY, f"{ip}.xml"),
    ]
    try:
        result = subprocess.run(download_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Download failed: {result.stderr}")
        return True
    except Exception as e:
        logging.error(f"Error downloading config from {ip}: {str(e)}")
        return False
    
def parse_xml_files(directory):
    ssid_key_pairs = []

    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            file_path = os.path.join(directory, filename)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                ssid = root.find(".//Value[@Name='WLAN1_SSID']")
                ssid_5g = root.find(".//Value[@Name='ssid']")
                keypassphrase_element = root.find(".//Value[@Name='wpaPSK']")

                if ssid_5g is not None and keypassphrase_element is not None:
                    ssid = ssid.attrib.get("Value", "")
                    ssid_5g = ssid_5g.attrib.get("Value", "")
                    keypassphrase = keypassphrase_element.attrib.get("Value", "")
                    ip = filename.replace(".xml", "")
                    ssid_key_pairs.append((ip, ssid, ssid_5g, keypassphrase))
            except ET.ParseError as e:
                logging.error(f"Error parsing XML file {file_path}: {e}")

    return ssid_key_pairs


def save_to_csv(pairs, output_file):
    sorted_pairs = sorted(pairs, key=lambda x: x[0])
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP", "SSID", "SSID-5G", "KeyPassphrase"])
        writer.writerows(sorted_pairs)

def main():
    # Create necessary directories first
    ensure_directories()
    
    failed_operations = []
    
    try:
        with open("./ips/sopto.txt", "r") as file:
            ip_list = [ip.strip() for ip in file.readlines()]
    except FileNotFoundError:
        logging.error("sopto.txt not found")
        return
        
    with ThreadPoolExecutor(max_workers=5) as executor:
        for ip in ip_list:
            try:
                if send_login_request(ip):
                    if download_config(ip):
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
        logging.info("All operations successful")
        
    pairs = parse_xml_files(XML_DIRECTORY)  # Updated to use constant
    save_to_csv(pairs, "./csv/sopto.csv")

if __name__ == "__main__":
    main()