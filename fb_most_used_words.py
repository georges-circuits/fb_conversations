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
    chars_f = ['á', 'ď', 'í', 'č', 'ť', 'ó', 'ő', 'ö', 'ú', 'ů', 'ř', 'ň', 'é', 'ý', 'ě', 'š', 'ž'] #"áďíčťóőöúůřňéýěšřž"
    chars_t = ['a', 'd', 'i', 'c', 't', 'o', 'o', 'o', 'u', 'u', 'r', 'n', 'e', 'y', 'e', 's', 'z'] #"adictooouurneyesrz"
    s = input.lower()
    for i in range(len(chars_f)):
        s = s.replace(chars_f[i], chars_t[i])
    s = re.sub(r'[^a-z ]', "", s)
    return s

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert fb inbox in json to .csv file')
    parser.add_argument('-fi', dest='input', required=False, default='message_1.json', help='Input filename')
    parser.add_argument('-fo', dest='output', required=False, default='output.csv', help='Output filename')
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
        print("Creating " + args.output) #, end='')
    
    """ with open(out_file_path, "w") as file:
        file.write(''.join(["window: ", args.days, " days;threshold: ", args.threshold, " messages per chat;\n"]))
        print(" ...done") """


    basepath = args.path_in
    print("Creating dictionary...")
    words = {}
    for entry in tqdm(os.listdir(basepath)):
        file_path = os.path.join(basepath, entry)
        if os.path.isdir(file_path):
            file_path += '/' + args.input

            if debug:
                print("Loading from: " + file_path, end='')
            try:
                """ with open(file_path, "r") as read_f:
                    data = json.load(read_f) """
                fix_mojibake_escapes = partial(re.compile(rb'\\u00([\da-f]{2})').sub, lambda m: bytes.fromhex(m.group(1).decode()))
                with open(file_path, 'rb') as binary_data:
                    repaired = fix_mojibake_escapes(binary_data.read())
                data = json.loads(repaired.decode('utf8'))
            except:
                print(" ...file" + args.input + " not found, exitting")
                sys.exit()
            messages = data['messages']
            num_messages = len(messages)

            for i in range(num_messages):
                if "content" in messages[i]:
                    message = (convert(messages[i]['content'])).split(" ")
                    for word in message:
                        if len(word) > 1 and len(word) < 20:
                            if word in words:
                                words[word] += 1
                            else:
                                words[word] = 1
            if debug:
                print(" ...completed")
            
    print("Writing all " + str(len(words)) + " words to a file...")
    with open(out_file_path[0:-4] + "_nsrt.txt", "w") as file_out:
        i = 0
        for word in words:
            i += 1
            file_out.write(str(i) + ". " + str(word) + ": " + str(words[word]) + "\n")
            #print(str(i) + ". " + str(word) + ": " + str(words_sorted[word]))
    
    print("Sorting...")
    words_sorted = {}
    #for i in tqdm(range(len(words))):
    for i in tqdm(range(1000)):
        max = 0
        max_key = ""
        for word in words:
            if max < words[word]:
                max = words[word]
                max_key = word
        words.pop(max_key)
        words_sorted[max_key] = max
    
    with open(out_file_path[0:-4] + ".txt", "w") as file_out:
        i = 0
        for word in words_sorted:
            i += 1
            file_out.write(str(i) + ". " + str(word) + ": " + str(words_sorted[word]) + "\n")
            #print(str(i) + ". " + str(word) + ": " + str(words_sorted[word]))
            
    print("done")

