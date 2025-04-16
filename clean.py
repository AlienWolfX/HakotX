#!/bin/python3

import os
import glob

def delete_files_in_directories(directory_paths):
    """Delete XML files in the specified directories."""
    for directory in directory_paths:
        if not os.path.isdir(directory):
            print(f"Directory not found: {directory}")
            continue
        for xml_file in glob.glob(os.path.join(directory, "*.xml")):
            if os.path.isfile(xml_file):
                os.remove(xml_file)
                print(f"Deleted file: {xml_file}")

def delete_files_by_extension(directory, extension):
    """Delete files with specified extension in the given directory."""
    for file in glob.glob(os.path.join(directory, f"*.{extension}")):
        if os.path.isfile(file):
            os.remove(file)
            print(f"Deleted file: {file}")

directory_paths = [
    "boa_xml/",
    "home_xml/",
    "luci_conf/",
    "sopto_xml/",
    "mini_xml/",
    "realtek_xml/",
    "uniway_xml/",
]

# Delete CSV and TXT files in current directory
delete_files_by_extension(".", "csv")
delete_files_by_extension(".", "txt")

# Delete XML files in specified directories
delete_files_in_directories(directory_paths)
print("Done!")
