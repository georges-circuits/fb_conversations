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


class Meta:
    def __init__(self, num_messages):
        self.num_messages = num_messages

class User:
    def __init__(self, name, Meta, messages):
        self.name = name
        self.Meta = Meta
        # I guess it works
        try:
            self.messages.append(messages)
        except:
            self.messages = []
            self.messages.append(messages)

    def check_existing(Users, name):
        for i in range(len(Users)):
            if name == Users[i].name:
                return i
        return -1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze data downloaded from facebook')
    parser.add_argument('-i', dest='path_in', required=True, default='', help='Path to the inbox folder')
    parser.add_argument('-o', dest='path_out', required=False, default='', help='Path to the output folder')

    args = parser.parse_args()

    fb_json_file_name = "message_1.json"
    debug = False
    Users = []

    skipped_chats = 0
    basepath = args.path_in
    print("Loading files...")
    for entry in tqdm(os.listdir(basepath)):
        file_path = os.path.join(basepath, entry)
        if os.path.isdir(file_path):
            file_path += '/' + fb_json_file_name
            try:
                # courtesy of StackOverflow
                fix_mojibake_escapes = partial(re.compile(rb'\\u00([\da-f]{2})').sub, lambda m: bytes.fromhex(m.group(1).decode()))
                with open(file_path, 'rb') as binary_data:
                    repaired = fix_mojibake_escapes(binary_data.read())
                data = json.loads(repaired.decode('utf8'))
            except:
                print("File" + fb_json_file_name + " not found, loading failed.")
                sys.exit()

            # ignore groups and other missleading data
            if len(data["participants"]) == 2:
                messages = data["messages"]
                user_name = data["participants"][0]["name"]
                num_messages = len(messages)

                check = User.check_existing(Users, user_name)
                if (check == -1):
                    Users.append(User(user_name, Meta(num_messages), messages))
                else:
                    (Users[check].messages).append(messages)
                    Users[check].Meta.num_messages += num_messages
            else:
                skipped_chats += 1


    print(len(Users))
    for user in Users:
        # print(user.name + ": ", end="")
        # print(user.Meta.num_messages)
        # print(len(user.messages))
        if len(user.messages) > 1:
            print("Same username with multiple folders found: " + user.name)
            print("Number of messages in each folder: ", end="")
            for i in user.messages:
                print(str(len(i)) + ", ", end="")
            print("in total: " + str(user.Meta.num_messages))
            print("")
    print("Skipped chats: " + str(skipped_chats))


