import json
import argparse
import sys
import os
import time
import datetime
from tqdm import tqdm
import re
from functools import partial


def ask_Y_n():
    print("Continue? [Y/n] ", end='')
    if "n" in input():
        quit()

def convert(input):
    chars_f = ['á', 'ď', 'í', 'č', 'ť', 'ó', 'ő', 'ö', 'ú', 'ů', 'ř', 'ň', 'é', 'ý', 'ě', 'š', 'ž', 'Ě', 'Š', 'Č', 'Ř', 'Ž', 'Ý', 'Á', 'Í', 'É', 'Ť', 'Ď', 'Ú', 'Ů', 'Ň']
    chars_t = ['a', 'd', 'i', 'c', 't', 'o', 'o', 'o', 'u', 'u', 'r', 'n', 'e', 'y', 'e', 's', 'z', 'E', 'S', 'C', 'R', 'Z', 'Y', 'A', 'I', 'E', 'T', 'D', 'U', 'U', 'N']
    s = input
    for i in range(len(chars_f)):
        s = s.replace(chars_f[i], chars_t[i])
    return s

class User:
    def __init__(self, name, meta, messages):
        self.name = name
        self.meta = meta
        self.messages = messages

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert fb inbox in json to .csv file')
    parser.add_argument('-fi', dest='input', required=False, default='message_1.json', help='Input filename')
    parser.add_argument('-fo', dest='output', required=True, default='output.csv', help='Output filename')
    parser.add_argument('-pi', dest='path_in', required=False, default='', help='Path to the inbox folder')
    parser.add_argument('-po', dest='path_out', required=False, default='', help='Path to the output folder')
    parser.add_argument('-d', dest='days', required=False, default='1', help='Count window in days')
    parser.add_argument('-v', dest='debug', required=False, default='', help='Prints more info')
    parser.add_argument('-t', dest='threshold', required=False, default='0', help='Min amount of messages per chat threshold')
    parser.add_argument('-a', dest='anon', required=False, default='', help='Anonymize')

    args = parser.parse_args()

    debug = 0
    if args.debug:
        debug = 1

    out_file_path = args.output
    if args.path_out:
        out_file_path = args.path_out + args.output
    
    if os.path.exists(out_file_path):
        print("File " + out_file_path + " already exists and will be overwritten")
        ask_Y_n()
    else:
        print("Creating " + args.output, end='')

    with open(out_file_path, "w") as file:
        file.write(''.join(["window: ", args.days, " days;threshold: ", args.threshold, " messages per chat;\n"]))
        print(" ...done")

    #print(os.getcwd();

    start_find_timestamp = time.time()
    lowest_timestamp = 9999999999999
    highest_timestamp = 0
    max_messages = 0
    total_messages = 0
    total_contacts = 0
    skipped_contacts = 0
    total_files = 0
    basepath = args.path_in
    print("Finding limits...")
    for entry in tqdm(os.listdir(basepath)):
        total_files += 1
        file_path = os.path.join(basepath, entry)
        if os.path.isdir(file_path):
            file_path += '/' + args.input
            if debug:
                print("Loading from: " + file_path, end='')
            try:
                fix_mojibake_escapes = partial(re.compile(rb'\\u00([\da-f]{2})').sub, lambda m: bytes.fromhex(m.group(1).decode()))
                with open(file_path, 'rb') as binary_data:
                    repaired = fix_mojibake_escapes(binary_data.read())
                data = json.loads(repaired.decode('utf8'))
            except:
                print(" ...file" + args.input + " not found, exitting")
                sys.exit()

            messages = data['messages']
            num_messages = len(messages)
            total_contacts += 1

            if num_messages >= int(args.threshold):
                if num_messages > max_messages:
                    max_messages = num_messages
                total_messages += num_messages
                
                for i in range(num_messages):
                    timestamp = messages[i]['timestamp_ms']
                    if timestamp < lowest_timestamp:
                        lowest_timestamp = timestamp
                    if timestamp > highest_timestamp:
                        highest_timestamp = timestamp
                if debug:
                    print(" ...completed")
            else:
                skipped_contacts += 1
                if debug:
                    print(" ...skipped")
    
    start_find_timestamp = round((time.time() - start_find_timestamp), 3)
    print("Elapsed time: " + str(start_find_timestamp) + "seconds")
    print()

    print("Total files found: " + str(total_files))
    print("Oldest massage: " + (str(datetime.datetime.fromtimestamp(lowest_timestamp / 1000))[:-7]))
    print("Newest massage: " + (str(datetime.datetime.fromtimestamp(highest_timestamp / 1000))[:-7]))
    timestamp_diff = round((highest_timestamp - lowest_timestamp) / 3600000)
    print("timestamp_diff: " + str(timestamp_diff) + "hours", end='')
    timestamp_diff = round(timestamp_diff / (24 * 365.25), 2)
    print(" or " + str(timestamp_diff) + "years")
    print("total_contacts: " + str(total_contacts), end='')
    print(" from that " + str(skipped_contacts) + " skipped")
    print("total_messages: " + str(total_messages))
    print("max_messages: " + str(max_messages))
    print()
    ask_Y_n()

    print("Opening " + args.output, end='')
    with open(out_file_path, "a") as file:
        print(" ...done")
        one_day_ms = 24 * 3600 * 1000 * int(args.days) # one day in ms
        day_ms = lowest_timestamp
        day_count = 0
        
        print("Calculating window", end='')
        days = "Window_num:;"
        while day_ms < highest_timestamp:
            day_count += 1
            day_ms += one_day_ms
            days += (''.join([str(day_count), ";"]))
        file.write(days + '\n')
        print(" ...done: " + str(day_count) + " * " + args.days + " days")

    start_find_timestamp = time.time()
    basepath = args.path_in
    name_count = 1
    if args.anon:
        with open(out_file_path[0:-4] + ".txt", "w") as file_names:
            pass

    print("Counting messages per specified timeframe...")
    for entry in tqdm(os.listdir(basepath)):
        file_path = os.path.join(basepath, entry)
        if os.path.isdir(file_path):
            file_path += '/' + args.input
            if debug:
                print("Loading from: " + file_path, end='')
            try:
                fix_mojibake_escapes = partial(re.compile(rb'\\u00([\da-f]{2})').sub, lambda m: bytes.fromhex(m.group(1).decode()))
                with open(file_path, 'rb') as binary_data:
                    repaired = fix_mojibake_escapes(binary_data.read())
                data = json.loads(repaired.decode('utf8'))
            except:
                print(" ...file" + args.input + " not found, exitting")
                sys.exit()
            
            name_count += 1
            messages = data['messages']
            num_messages = len(messages)
            if num_messages >= int(args.threshold):
                messages_this_day = 0
                name = data['participants'][0]['name']

                if args.anon:
                    with open(out_file_path[0:-4] + ".txt", "a") as file_names:
                        file_names.write(''.join(["User", str(name_count), ": ", name, "\n"]))
                    name = "User" + str(name_count)
                
                file_line = convert(name) + ":;"
                last_m = 0

                with open(out_file_path, "a") as file:
                    for day in range(day_count):
                        m = last_m
                        while m < num_messages:
                            m += 1
                            m_json = num_messages - m
                            timestamp = messages[m_json]['timestamp_ms']
                            if timestamp >= lowest_timestamp + (day * one_day_ms) and timestamp < (lowest_timestamp + ((day + 1) * one_day_ms)):
                                messages_this_day += 1
                            if timestamp > (lowest_timestamp + ((day + 1) * one_day_ms)): 
                                last_m = m - 1
                                #print(last_m)
                                break
                        file_line += (''.join([str(messages_this_day), ";"]))
                        messages_this_day = 0
                    file_line = ''.join([file_line, "\n"])
                    #print(file_line)
                    file.write(file_line)
                    if debug:
                        print(" ...completed")
                    #print()
                    # FIXME: prepsat to na neco vic pythonovskeho - nejspis bych prvni udelal array s tim poctem zprav za obdobi a potom to formatoval
                    # treba by slo udelat referencni body, spocitat kolik je zprav mezi nema a skocit na dalsi nez jit takto po zpravach
            elif debug:
                print(" ...skipped")
    
    
    start_find_timestamp = round((time.time() - start_find_timestamp), 3)
    print("Elapsed time: " + str(start_find_timestamp) + "seconds")
