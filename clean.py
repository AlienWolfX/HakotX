#!/bin/python3

import os
import glob

def delete_files_in_directories(directory_paths):
    for directory in directory_paths:
        if not os.path.isdir(directory):
            print(f"Directory not found: {directory}")
            continue
        for xml_file in glob.glob(os.path.join(directory, "*.xml")):
            if os.path.isfile(xml_file):
                os.remove(xml_file)
                print(f"Deleted file: {xml_file}")


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
]

delete_csv_files_in_directory(".")
delete_files_in_directories(directory_paths)
print("Done!")
