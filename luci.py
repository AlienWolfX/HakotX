import os
import telnetlib
import csv

USERNAME = "root"
PASSWORD = "rootktcatv"


def find_option_value(option_name, file_content, start_index):
    option_index = file_content.find(option_name, start_index)
    if option_index == -1:
        return "", -1

    end_index = file_content.find("\n", option_index)
    value = file_content[option_index:end_index].strip()
    value = value.split()[2][1:-1]  # Extract the value between single quotes

    return value, end_index


def telnet_login(host, username, password):
    # Connect to the Telnet server
    tn = telnetlib.Telnet(host)

    # Wait for the login prompt
    tn.read_until(b"ktcatv login: ")
    print("Received login prompt")

    # Send the username
    tn.write(username.encode("utf-8") + b"\n")
    print("Sent username")

    # Wait for the password prompt
    tn.read_until(b"Password: ")
    print("Received password prompt")

    # Send the password
    tn.write(password.encode("utf-8") + b"\n")
    print("Sent password")

    # Wait for the command prompt
    tn.read_until(b"# ")
    print("Received command prompt")

    return tn


def execute_command(tn, command):
    # Send the command
    tn.write(command.encode("utf-8") + b"\n")
    print("Sent command:", command)

    # Wait for the command output
    tn.read_until(b" ")
    output = tn.read_until(b"# ").decode("utf-8")
    print("Received command output")

    return output


def tocsv():
    luci_conf_folder = "luci_conf"
    csv_file = "luci.csv"

    # Get the list of files in luci_conf folder
    file_names = os.listdir(luci_conf_folder)

    # Open the CSV file for writing
    with open(csv_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP Address", "SSID", "Key"])

        # Process each file in luci_conf folder
        for file_name in file_names:
            file_path = os.path.join(luci_conf_folder, file_name)

            # Read the content of the file
            with open(file_path, "r") as f:
                file_content = f.read()

            # Find option ssid value
            ssid = find_option_value("option ssid", file_content, 0)[0]

            # Find option key value (second instance)
            key_start_index = 0
            key_count = 0
            while True:
                key, key_end_index = find_option_value(
                    "option key", file_content, key_start_index
                )
                if not key:
                    break
                key_start_index = key_end_index
                key_count += 1
                if key_count == 2:
                    # Write the data to the CSV file
                    ip_address = file_name[:-4]  # Remove the .txt extension
                    writer.writerow([ip_address, ssid, key])
                    break


def main():
    # Read IP addresses from luci.txt file
    with open("luci.txt", "r") as file:
        ip_addresses = file.read().splitlines()

    # Create luci_conf directory if it doesn't exist
    os.makedirs("luci_conf", exist_ok=True)

    for ip_address in ip_addresses:
        tn = telnet_login(ip_address, USERNAME, PASSWORD)
        command_output = execute_command(tn, "uci export")
        filename = f"luci_conf/{ip_address}.txt"
        with open(filename, "w") as file:
            file.write(command_output)
        tn.close()

        print(f"Configuration exported for IP: {ip_address}. Saved to: {filename}")
    tocsv()


if __name__ == "__main__":
    main()
