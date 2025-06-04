import os
import telnetlib
import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("LUCI_USERNAME")
password = os.getenv("LUCI_PASSWORD")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USERNAME = username
PASSWORD = password
LUCI_CONF_FOLDER = "./luci_conf"
CSV_FILE = "./csv/luci_pass.csv"

def find_option_value(option_name, file_content, start_index):
    option_index = file_content.find(option_name, start_index)
    if option_index == -1:
        return "", -1

    end_index = file_content.find("\n", option_index)
    value = file_content[option_index:end_index].strip()
    value = value.split()[2][1:-1] 

    return value, end_index

def telnet_login(host, username, password):
    try:
        tn = telnetlib.Telnet(host)

        tn.read_until(b"ktcatv login: ")
        tn.write(username.encode("utf-8") + b"\n")

        tn.read_until(b"Password: ")
        tn.write(password.encode("utf-8") + b"\n")

        tn.read_until(b"# ")
        logging.info(f"Logged into {host} successfully")

        return tn
    except Exception as e:
        logging.error(f"Failed to login to {host}: {str(e)}")
        return None

def execute_command(tn, command):
    try:
        tn.write(command.encode("utf-8") + b"\n")
        tn.read_until(b" ")
        output = tn.read_until(b"# ").decode("utf-8")
        logging.info("Command executed successfully")

        return output
    except Exception as e:
        logging.error(f"Failed to execute command: {str(e)}")
        return ""

def save_configuration(ip_address, content):
    try:
        filename = os.path.join(LUCI_CONF_FOLDER, f"{ip_address}.txt")
        with open(filename, "w") as file:
            file.write(content)
        logging.info(f"Configuration saved for IP: {ip_address}")
    except Exception as e:
        logging.error(f"Failed to save configuration for {ip_address}: {str(e)}")

def process_ip(ip_address):
    tn = telnet_login(ip_address, USERNAME, PASSWORD)
    if tn:
        command_output = execute_command(tn, "uci export")
        save_configuration(ip_address, command_output)
        tn.close()

def tocsv():
    file_names = os.listdir(LUCI_CONF_FOLDER)

    try:
        with open(CSV_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["IP Address", "SSID", "KeyPassphrase"])

            for file_name in file_names:
                file_path = os.path.join(LUCI_CONF_FOLDER, file_name)

                with open(file_path, "r") as f:
                    file_content = f.read()

                ssid = find_option_value("option ssid", file_content, 0)[0]

                key_start_index = 0
                key_count = 0
                while True:
                    key, key_end_index = find_option_value("option key", file_content, key_start_index)
                    if not key:
                        break
                    key_start_index = key_end_index
                    key_count += 1
                    if key_count == 2:
                        ip_address = file_name[:-4]  # Remove the .txt extension
                        writer.writerow([ip_address, ssid, key])
                        break
        logging.info(f"Data written to CSV file {CSV_FILE}")
    except Exception as e:
        logging.error(f"Failed to write to CSV file: {str(e)}")

def main():
    with open("./ips/luci.txt", "r") as file:
        ip_addresses = file.read().splitlines()

    os.makedirs(LUCI_CONF_FOLDER, exist_ok=True)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_ip, ip): ip for ip in ip_addresses}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"An error occurred during processing: {str(e)}")

    tocsv()

if __name__ == "__main__":
    main()
