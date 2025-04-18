import os
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
XML_DIRECTORY = "gpnf14c_xml"
USERNAME = os.getenv("GPNF14C_USERNAME", "super")
PASSWORD = os.getenv("GPNF14C_PASSWORD", "kingT%2392Su")

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

def main():
    """Main function to process IPs from file."""
    ensure_directories()
    
    try:
        with open("gpnf14c.txt", "r") as f:
            ip_list = [ip.strip() for ip in f.readlines()]
    except FileNotFoundError:
        logging.error("gpnf14c.txt not found")
        return
    
    failed_ips = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        for ip in ip_list:
            try:
                if not login_and_download(ip):
                    failed_ips.append(ip)
            except Exception as e:
                logging.error(f"Failed to process {ip}: {str(e)}")
                failed_ips.append(ip)
    
    if failed_ips:
        logging.info("Failed operations:")
        for ip in failed_ips:
            logging.info(f"- {ip}")
    else:
        logging.info("All operations completed successfully")

if __name__ == "__main__":
    main()