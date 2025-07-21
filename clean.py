#!/bin/python3

import os
import glob
from datetime import datetime
import zipfile
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def delete_files_in_directories(directory_paths):
    """Delete XML files in the specified directories."""
    for directory in directory_paths:
        if not os.path.isdir(directory):
            logging.info(f"Directory not found: {directory}")
            continue
        for xml_file in glob.glob(os.path.join(directory, "*.xml")):
            if os.path.isfile(xml_file):
                os.remove(xml_file)
                logging.info(f"Deleted file: {xml_file}")
        for txt_file in glob.glob(os.path.join(directory, "*.txt")):
            if os.path.isfile(txt_file):
                os.remove(txt_file)
                logging.info(f"Deleted file: {txt_file}")

def delete_files_by_extension(directory, extension):
    """Delete files with specified extension in the given directory."""
    for file in glob.glob(os.path.join(directory, f"*.{extension}")):
        if os.path.isfile(file):
            os.remove(file)
            print(f"Deleted file: {file}")

directory_paths = [
    "realtek_xml/",
    "uniway_xml/",
    # "onu4fer1tvaswb_xml/", commented out as it needs review
    "pn_bh2_03_02_xml/",
    "spu_ge22wd_h_xml/",  
    "xpn_rh2_00-07_xml/",  
    "ar9331_conf/",
    "gpnf14c_xml/",  
]

def compress_csv_files(source_dir, dest_dir):
    """Compress all CSV files from source directory into a single ZIP file with CONFIG-DATE format."""
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    zip_filename = f"CONFIG-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.zip"
    zip_path = os.path.join(dest_dir, zip_filename)
    
    csv_files = glob.glob(os.path.join(source_dir, "*.csv"))
    
    if csv_files:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for csv_file in csv_files:
                filename = os.path.basename(csv_file)
                zipf.write(csv_file, filename)
                logging.info(f"Added to archive: {filename}")
        logging.info(f"Created archive: {zip_path}")
    else:
        logging.info("No CSV files found to compress")

compress_csv_files("./csv", "./csv_backup")

delete_files_by_extension("./csv", "csv")
delete_files_in_directories(directory_paths)
logging.info("Done!")