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
        for txt_file in glob.glob(os.path.join(directory, "*.txt")):
            if os.path.isfile(txt_file):
                os.remove(txt_file)
                print(f"Deleted file: {txt_file}")

def delete_files_by_extension(directory, extension):
    """Delete files with specified extension in the given directory."""
    for file in glob.glob(os.path.join(directory, f"*.{extension}")):
        if os.path.isfile(file):
            os.remove(file)
            print(f"Deleted file: {file}")

directory_paths = [
    "realtek_xml/",
    "uniway_xml/",
    # "onu4fer1tvaswb_xml/",
    "pn_bh2_03_02_xml/",
    "spu_ge22wd_h_xml/",  
    "xpn_rh2_00-07_xml/",  
    "ar9331_conf/",
    "gpnf14c_xml/",  
]

# Creates a copy of the csv




delete_files_by_extension("./csv", "csv")

# Delete XML files in specified directories
delete_files_in_directories(directory_paths)
print("Done!")
