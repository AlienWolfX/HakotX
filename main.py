import concurrent.futures
import socket
import subprocess
import logging
import ipaddress

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_ip(ip):
    """Checks if the specified IP address is alive."""
    try:
        socket.setdefaulttimeout(2)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, 80))
        return ip, True
    except (socket.timeout, ConnectionRefusedError, socket.error) as e:
        logging.debug(f"IP {ip} check failed: {e}")
        return ip, False

def process_ip_range(ip_range):
    """Processes a range of IP addresses and returns lists of alive and dead IPs."""
    alive_ips = []
    dead_ips = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_ip, ip): ip for ip in ip_range}

        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            try:
                ip, is_alive = future.result()
                if is_alive:
                    alive_ips.append(ip)
                    logging.info(f"IP {ip} is alive")
                else:
                    dead_ips.append(ip)
                    logging.info(f"IP {ip} is dead")
            except Exception as e:
                logging.error(f"Error processing IP {ip}: {e}")

    return alive_ips, dead_ips

def main():
    """Main function that processes a range of IP addresses and saves the results to files."""
    ip_range = [str(ip) for ip in ipaddress.IPv4Network('172.18.0.0/20')]

    logging.info("Starting IP range processing.")
    alive_ips, dead_ips = process_ip_range(ip_range)
    
    try:
        with open("alive.txt", "w") as alive_file:
            alive_file.write("\n".join(alive_ips))
        logging.info("Alive IPs saved to alive.txt.")
    except Exception as e:
        logging.error(f"Failed to save alive IPs: {e}")

    try:
        with open("dead.txt", "w") as dead_file:
            dead_file.write("\n".join(dead_ips))
        logging.info("Dead IPs saved to dead.txt.")
    except Exception as e:
        logging.error(f"Failed to save dead IPs: {e}")

    try:
        subprocess.run(["mv", "*.csv", "csv/"], shell=True, check=True)
        subprocess.run(["python", "clean.py"], check=True)
        subprocess.run(["python", "sep.py"], check=True)
        logging.info("Subprocesses completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess failed: {e}")

if __name__ == "__main__":
    main()
    logging.info("Done!")