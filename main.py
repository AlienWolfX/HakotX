import concurrent.futures
import socket
import subprocess
import logging

logging.basicConfig(level=logging.INFO)


def check_ip(ip):
    """Checks if the specified IP address is alive."""
    try:
        socket.setdefaulttimeout(10)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((ip, 80))
        return ip, True
    except (socket.timeout, ConnectionRefusedError, socket.error):
        return ip, False


def process_ip_range(ip_range):
    """Processes a range of IP addresses and returns lists of alive and dead IPs."""
    alive_ips = []
    dead_ips = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(check_ip, ip) for ip in ip_range]

        for future in concurrent.futures.as_completed(futures):
            ip, is_alive = future.result()
            if is_alive:
                alive_ips.append(ip)
                logging.info(f"IP {ip} is alive")
            else:
                dead_ips.append(ip)
                logging.info(f"IP {ip} is dead")

    return alive_ips, dead_ips


def main():
    """Main function that processes a range of IP addresses and saves the results to files."""
    ip_range = [f"172.18.{i}.{j + 1}" for i in range(20) for j in range(256)]

    alive_ips, dead_ips = process_ip_range(ip_range)

    with open("alive.txt", "w") as alive_file:
        alive_file.write("\n".join(alive_ips))

    with open("dead.txt", "w") as dead_file:
        dead_file.write("\n".join(dead_ips))

    logging.info("Results saved in alive.txt and dead.txt.")


if __name__ == "__main__":
    main()
    subprocess.run(["mv", "*.csv", "csv/"], shell=True)
    subprocess.run(["python", "clean.py"])
    subprocess.run(["python", "sep.py"])
    logging.info("Done!")
