# HakotX

![License](https://img.shields.io/badge/license-MIT-blue.svg)

HakotX is a collection of Python scripts designed to streamline the process of fetching ONU (Optical Network Unit) configuration files over a network. This automation tool simplifies and accelerates the retrieval of ONU configurations.

## Overview

HakotX includes the following Python scripts:

- **main.py:** Checks the status (alive or dead) of IP addresses.
- **clean.py:** Deletes outdated fetched data.
- **sep.py:** Separates alive IP addresses into their corresponding device types.
- **boa.py:** Gathers configuration files for KingType boa-based web servers.
- **mini.py:** Gathers configuration files for KingType minihttpd-based web servers.
- **luci.py:** Gathers configuration for KingType LuCi-based web servers.
- **home.py:** Gathers configuration for a generic boa-based web server.
- **realtek.py:** Gathers configuration for a VSOL boa-based web server.
- **uniway.py:** Gathers configuration for a UNIWAY boa-based web server.

Feel free to explore and utilize these scripts based on your specific network requirements.

## Getting Started

### Prerequisites

- Python 3.x installed
- Install required dependencies:

  ```bash
  pip install -r requirements.txt
  ```
