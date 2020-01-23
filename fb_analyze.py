import json
import argparse
import sys
import os
import glob
import time
import datetime
from tqdm import tqdm
import re
from functools import partial

def ask_Y_n():
    print("Continue? [Y/n] ", end='')
    if "n" or "N" in input():
        return False
    return True

def print_numbered_menu(menu):
    while True:
        i = 0
        for item in menu:
            i += 1
            print(str(i) + ". " + item)
        if i == 1:
            print("Chose 1: ", end="")
        else:
            print("Chose 1 to " + str(i) + ": ", end="")
        u_in = input()
        if u_in.isdigit():
            u_in = int(u_in)
            if u_in >= 1 and u_in <= i:
                return u_in
            else:
                print("\nInput must be within the said range")
        else:
            print("\nOnly digits allowed")

def abort():
    print("Aborting!")
    sys.exit()


class Meta:
    def __init__(self, participants, num_messages, path):
        par = []
        for p in participants:
            par.append(p["name"])
        self.participants = par
        self.num_messages = num_messages
        self.path = path
    
    def print(self):
        print("participants: " + str(self.participants))
        print("num_messages: " + str(self.num_messages))
        print("path: " + self.path)

class File:
    def __init__(self, Meta, messages):
        self.Meta = Meta
        self.messages = messages

class User:
    def __init__(self, name, File, num_messages):
        self.name = name
        self.Files = File
        self.num_messages = num_messages

    def check_existing(users, name):
        for i in range(len(users)):
            if name == users[i].name:
                return i
        return -1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze data downloaded from facebook')
    parser.add_argument('-i', dest='path_in', required=True, default='', help='Path to the inbox folder')
    parser.add_argument('-o', dest='path_out', required=False, default='', help='Path to the output folder')

    args = parser.parse_args()

    debug = False
    users = []
    basepath = args.path_in
    total_messages = 0
    skipped_messages = 0
    skipped_chats = 0

    print("Loading files...")
    # iterate through all user folders
    for entry in tqdm(os.listdir(basepath)):
        file_path = os.path.join(basepath, entry)
        if os.path.isdir(file_path):
            # iterate through all .json files
            for file_name in glob.glob(os.path.join(file_path, "*.json")):

                # courtesy of StackOverflow (fixes the cursed character encoding)
                fix_mojibake_escapes = partial(re.compile(rb'\\u00([\da-f]{2})').sub, lambda m: bytes.fromhex(m.group(1).decode()))
                with open(file_name, 'rb') as binary_data:
                    repaired = fix_mojibake_escapes(binary_data.read())
                data = json.loads(repaired.decode('utf8'))

                # parse the important data
                messages = data["messages"]
                user_name = data["participants"][0]["name"]
                num_messages = len(messages)

                # ignore groups
                if data["thread_type"] == "Regular":
                    total_messages += num_messages

                    # check whether the user is already in the users array
                    check = User.check_existing(users, user_name)
                    meta_info = Meta(data["participants"], num_messages, file_name)
                    file = File(meta_info, messages)
                    if (check == -1):
                        # add new user
                        users.append(User(user_name, [file], num_messages))
                    else:
                        # add another message file (thanks fb) and update the meta info
                        users[check].Files.append(file)
                        users[check].num_messages += num_messages
                else:
                    skipped_chats += 1
                    skipped_messages += num_messages

    
    # second participant should always be the sender (should be the same acros all files)
    # name_check_ref = users[0].Meta.participants[1]["name"]
    # for user in users:
    #     if user.Meta.participants[1]["name"] != name_check_ref:
    #         print("Sender\'s name does not match up every time!")
    #         print("Should be " + name_check_ref + " but " + user.Meta.participants[1]["name"] + " found instead")
    #         print("Found in:")
    #         user.Meta.print()
    #         abort()


    print("Skipped chats: " + str(skipped_chats) + " (" + str(skipped_messages) + " messages)")
    print("Total loaded messages: " + str(total_messages))

    while True:
        option = print_numbered_menu(["Exit", "Count messages per timeframe", "Compile a list of most used words", "Print stats"])
        if option == 1:
            sys.exit()
        elif option == 2:
            pass
        elif option == 3:
            pass
        elif option == 4:
            print("users: " + str(len(users)))
            # for user in users:
            #     print(user.name + ": " + str(user.Meta.num_messages) + " (files: " + str(user.Meta.num_files) + ")")
            #     if user.Meta.num_files > 1:
            #         print("Number of messages in each folder: ", end="")
            #         for m in user.messages:
            #             print(str(len(m)) + ", ", end="")
            # print()
            for user in users:
                print(user.name + ": " + str(user.num_messages) + " in " + str(len(user.Files)) + " files")
                for file in user.Files:
                    print(file.Meta.participants, file.Meta.num_messages)
                    print("Meta:")
                    file.Meta.print()
                print("")
        else:
            sys.exit()




