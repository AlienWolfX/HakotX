import os
import requests
import logging
import csv
import configparser
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load config properties
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', '.config.properties'))

XML_DIRECTORY = config.get('folders', 'gpnf14c_xml_folder', fallback='./gpnf14c_xml')
CSV_FOLDER = config.get('folders', 'csv_folder', fallback='./csv')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

USERNAME = os.getenv("GPNF14C_USERNAME")
PASSWORD = os.getenv("GPNF14C_PASSWORD")

def ensure_directories():
    """Create necessary directories if they don't exist."""
    try:
        os.makedirs(XML_DIRECTORY, exist_ok=True)
        logging.info(f"Directory {XML_DIRECTORY} is ready")
    except Exception as e:
        logging.error(f"Failed to create directory {XML_DIRECTORY}: {str(e)}")
        raise

def login_and_download(ip):
    """Login to device and download configuration."""
    session = requests.Session()
    
    # Headers for login
    login_headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": f"http://{ip}",
        "Referer": f"http://{ip}/login.asp",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    # Headers for config download
    download_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"http://{ip}",
        "Referer": f"http://{ip}/page/config.asp?0",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Login request
        login_url = f"http://{ip}/boaform/webLogin"
        login_data = {
            "username": USERNAME,
            "password": PASSWORD,
            "language": "0"
        }
        
        login_response = session.post(
            login_url, 
            headers=login_headers, 
            data=login_data,
            verify=False,
            timeout=5
        )
        
        if login_response.status_code != 200:
            logging.error(f"Login failed for {ip}: {login_response.status_code}")
            return False
            
        # Download configuration
        download_url = f"http://{ip}/boaform/settingConfig"
        download_data = {"config_backup": "Backup"}
        
        download_response = session.post(
            download_url,
            headers=download_headers,
            data=download_data,
            verify=False,
            timeout=5
        )
        
        if download_response.status_code == 200:
            # Save the configuration
            config_file = os.path.join(XML_DIRECTORY, f"{ip}.xml")
            with open(config_file, "wb") as f:
                f.write(download_response.content)
            logging.info(f"Successfully downloaded configuration for {ip}")
            return True
        else:
            logging.error(f"Download failed for {ip}: {download_response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Error processing {ip}: {str(e)}")
        return False

def normalize_mac(mac):
    """Normalize MAC address to uppercase with colons."""
    mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
    if len(mac) >= 12:
        mac = mac[:12] 
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    return mac

def parse_xml_files():
    """Parse XML files and extract SSID and PSK values."""
    xml_dir = XML_DIRECTORY
    results = []

    # Check if directory exists
    if not os.path.exists(xml_dir):
        logging.error(f"Directory {xml_dir} not found")
        return results

    for filename in os.listdir(xml_dir):
        if not filename.endswith('.xml'):
            continue

        filepath = os.path.join(xml_dir, filename)
        ip = filename.replace('.xml', '')

        try:
            # Read file as text
            mac_addr = ''
            ssid_2g = ''
            psk_2g = ''
            ssid_5g = ''
            psk_5g = ''
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if 'Name="MacAddr"' in line:
                        mac_addr = normalize_mac(line.split('Value="')[1].split('"')[0])
                    elif 'Name="WLAN1_SSID"' in line:
                        ssid_2g = line.split('Value="')[1].split('"')[0]
                    elif 'Name="WLAN1_WPA_PSK"' in line:
                        psk_2g = line.split('Value="')[1].split('"')[0]
                    elif 'Name="SSID"' in line and not 'WLAN1_SSID' in line:
                        ssid_5g = line.split('Value="')[1].split('"')[0]
                    elif 'Name="WLAN_WPA_PSK"' in line:
                        psk_5g = line.split('Value="')[1].split('"')[0]

            if mac_addr or ssid_2g or psk_2g or ssid_5g or psk_5g:
                results.append([ip, mac_addr, ssid_2g, psk_2g, ssid_5g, psk_5g])
                logging.info(f"Processed {ip}")

        except Exception as e:
            logging.warning(f"Error processing {filepath}: {str(e)}")
            continue

    return results

def save_to_csv(data):
    """Save parsed results to CSV file."""
    output_file = os.path.join(CSV_FOLDER, "gpnf14c.csv")
    
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['IP', 'SSID_2G', 'PSK_2G', 'SSID_5G', 'PSK_5G'])
            writer.writerows(data)
        logging.info(f"Results saved to {output_file}")
    except Exception as e:
        logging.error(f"Failed to save CSV: {str(e)}")

def main():
    """Main function to process IPs from file."""
    ensure_directories()
    
    try:
        with open("./ips/gpnf14c.txt", "r") as f:
            ip_list = [ip.strip() for ip in f.readlines()]
    except FileNotFoundError:
        logging.error("gpnf14c.txt not found")
        return
    
    failed_ips = []
    
    # Download configurations
    with ThreadPoolExecutor(max_workers=5) as executor:
        for ip in ip_list:
            try:
                if not login_and_download(ip):
                    failed_ips.append(ip)
            except Exception as e:
                logging.error(f"Failed to process {ip}: {str(e)}")
                failed_ips.append(ip)
    
    if failed_ips:
        logging.info("Failed downloads:")
        for ip in failed_ips:
            logging.info(f"- {ip}")
    
    # Parse configurations and save to CSV
    logging.info("Starting XML parsing...")
    results = parse_xml_files()
    if results:
        save_to_csv(results)
        logging.info("XML parsing and CSV generation completed")
    else:
        logging.warning("No valid configurations found to parse")

if __name__ == "__main__":
    main()