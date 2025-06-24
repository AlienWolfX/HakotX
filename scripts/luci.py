import os
import csv
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import telnetlib
import configparser

load_dotenv()

username = os.getenv("LUCI_USERNAME")
password = os.getenv("LUCI_PASSWORD")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load config properties
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', '.config.properties'))

LUCI_CONF_FOLDER = config.get('folders', 'luci_conf_folder', fallback='./luci_conf')
CSV_FILE = os.path.join(config.get('folders', 'csv_folder', fallback='./csv'), "luci_pass.csv")

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
        if not isinstance(username, str) or not isinstance(password, str):
            raise ValueError("Username or password is not set or not a string.")

        tn = telnetlib.Telnet(host, 23, timeout=10)
        tn.read_until(b"login: ")
        tn.write(username.encode("utf-8") + b"\n")
        tn.read_until(b"Password: ")
        tn.write(password.encode("utf-8") + b"\n")
        logging.info(f"Logged into {host} successfully")
        return tn
    except Exception as e:
        logging.error(f"Failed to login to {host}: {str(e)}")
        return None

def execute_command(tn, command):
    try:
        # Flush any banner or prompt before sending the command
        tn.read_until(b"# ", timeout=10)
        tn.write(command.encode("utf-8") + b"\n")
        # Read until the prompt appears again (after command output)
        output = tn.read_until(b"# ", timeout=20)
        logging.info("Command executed successfully")
        # Remove the command echo and prompt from the output
        output_str = output.decode("utf-8", errors="ignore")
        # Optionally, remove the command itself and the prompt from the output
        output_lines = output_str.splitlines()
        # Remove the first line if it is the command echo
        if output_lines and output_lines[0].strip() == command:
            output_lines = output_lines[1:]
        # Remove the last line if it is the prompt
        if output_lines and output_lines[-1].strip().endswith("#"):
            output_lines = output_lines[:-1]
        return "\n".join(output_lines)
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
    tn = telnet_login(ip_address, username, password)
    if tn:
        # Flush banner and prompt after login
        try:
            tn.read_until(b"# ", timeout=10)
        except Exception:
            pass
        command_output = execute_command(tn, "uci export")
        save_configuration(ip_address, command_output)
        tn.close()

def tocsv():
    file_names = os.listdir(LUCI_CONF_FOLDER)

    try:
        with open(CSV_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["IP", "SSID_2G", "PSK_2G"])

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
                        ip_address = file_name[:-4] 
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
        list(executor.map(process_ip, ip_addresses))

    tocsv()

if __name__ == "__main__":
    main()
