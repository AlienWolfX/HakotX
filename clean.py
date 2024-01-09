#!/bin/python3

import os
import glob


def delete_files_in_directories(directory_paths):
    for directory in directory_paths:
        if not os.path.isdir(directory):
            print(f"Directory not found: {directory}")
            continue
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")


def delete_csv_files_in_directory(directory):
    for csv_file in glob.glob(os.path.join(directory, "*.csv")):
        if os.path.isfile(csv_file):
            os.remove(csv_file)
            print(f"Deleted file: {csv_file}")


directory_paths = [
    "boa_xml/",
    "home_xml/",
    "luci_conf/",
    "mini_xml/",
    "realtek_xml/",
    "uniway_xml/",
    "csv/",
]

delete_csv_files_in_directory(".")
delete_files_in_directories(directory_paths)
print("Done!")
