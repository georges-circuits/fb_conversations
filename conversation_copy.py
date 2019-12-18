import json
import argparse
import sys
import os
import time
from tqdm import tqdm

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy just the message_1.json files to anothe folder')
    parser.add_argument('-from', dest='path_in', required=True, default='', help='Path to the inbox folder')
    parser.add_argument('-to', dest='path_out', required=True, default='', help='Path to the output folder')
    parser.add_argument('-v', dest='debug', required=False, default='', help='Prints more info')

    args = parser.parse_args()

    debug = 0
    if args.debug:
        debug = 1

    for entry in tqdm(os.listdir(basepath)):
        total_files += 1
        file_path = os.path.join(basepath, entry)
        if os.path.isdir(file_path):
            file_path += '/' + args.input
            if debug:
                print("Loading from: " + file_path, end='')
            try:
                with open(file_path, "r") as read_f:
                    data = json.load(read_f)
            except:
                print(" ...file" + args.input + " not found, exitting")
                sys.exit()
