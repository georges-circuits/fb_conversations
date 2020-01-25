import json
import argparse
import sys
import os
import glob
import time
import re
from datetime import datetime
from tqdm import tqdm
from functools import partial

def ask_continue():
    print("Continue? [Y/n] ", end='')
    resp = input().lower()
    if "n" in resp:
        return False
    return True

def convert(input):
    chars_f = ['á', 'ď', 'í', 'č', 'ť', 'ó', 'ő', 'ö', 'ú', 'ů', 'ř', 'ň', 'é', 'ý', 'ě', 'š', 'ž'] #"áďíčťóőöúůřňéýěšřž"
    chars_t = ['a', 'd', 'i', 'c', 't', 'o', 'o', 'o', 'u', 'u', 'r', 'n', 'e', 'y', 'e', 's', 'z'] #"adictooouurneyesrz"
    s = input.lower()
    for i in range(len(chars_f)):
        s = s.replace(chars_f[i], chars_t[i])
    s = re.sub(r'[^a-z ]', "", s)
    return s

def convert_ms(value_ms):
    return datetime.utcfromtimestamp(value_ms / 1000).strftime('%d.%m.%Y %H:%M:%S')

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
    print("Aborting")
    sys.exit()

def check_output_folder(path):
    if not os.access(path, os.F_OK):
        os.mkdir(path)
        print("Created output folder")
    else: 
        print("Using existing output folder")

def check_existing(users, name):
    for i in range(len(users)):
        if name == users[i].name:
            return i
    return -1


class Meta:
    def __init__(self, participants, num_messages, path):
        # just so I do not have to use the "name" keyword
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
    def __init__(self, name, File, num_messages, selected = True):
        self.name = name
        self.Files = File
        self.num_messages = num_messages
        self.selected = selected

class Info:
    def __init__(self, skipped_messages, skipped_chats):
        self.skipped_messages = skipped_messages
        self.skipped_chats = skipped_chats
        self.output_name = ""
        self.oldest_timestamp = 0
        self.newest_timestamp = 0
        self.period = 0

class Analyze:
    def __init__(self, Users, num_messages, Info, ordered = False):
        self.Users = Users
        self.ordered = ordered
        self.num_messages = num_messages
        self.Info = Info


    def order(self):
        if self.ordered == False:
            sorted = False
            print ("Ordering chats based on ammount of messages...")
            if len(self.Users) > 1:
                while not sorted:
                    sorted = True
                    for i in range(len(self.Users) - 1):
                        if self.Users[i].num_messages < self.Users[i + 1].num_messages:
                            sorted = False
                            self.Users[i], self.Users[i + 1] = self.Users[i + 1], self.Users[i]
            self.ordered = True
        else:
            print ("Chats are already ordered")

    def print_stats(self):
        print("")
        print("Stats:")
        selected = 0
        selected_messages = 0
        for user in self.Users: 
            if user.selected: 
                selected += 1
                selected_messages += user.num_messages
        print ("Number of chats loaded: " + str(len(self.Users)) + " (" + str(selected) + " selected)")
        print ("Loaded messages: " + str(self.num_messages) + " (" + str(selected_messages) + " selected)")
        print ("Messages total: " + str(self.num_messages + self.Info.skipped_messages) + 
            " (not including " + str(self.Info.skipped_messages) + " in groups - skipped)")
        print ("Currently selected " + str(selected / len(self.Users) * 100) + "% of chats (" +
            str(selected_messages / self.num_messages * 100) + "% of messages)")

    def print_times(self):
        if self.Info.period == 0:
            self.find_edge_messages()
        print("\nTime stats (UTC):")
        print("Oldest message:", convert_ms(self.Info.oldest_timestamp))
        print("Newest message:", convert_ms(self.Info.newest_timestamp))
        print("Which totals a period of", self.Info.period / 1000 / 3600 / 24 / 365.25, "years")

    def check_sender_name(self):
        print("Checking names...")
        name_check_ref = self.Users[0].Files[0].Meta.participants[1]
        fault = False
        for user in self.Users:
            for file in user.Files:
                if file.Meta.participants[1] != name_check_ref:
                    print("Should be " + name_check_ref + " but " + file.Meta.participants[1] + " found instead")
                    print("Found in:")
                    file.Meta.print()
                    print("")
                    fault = True
        if fault:
            print("Sender\'s name does not match up every time!")
            if ask_continue() == False: 
                abort()

    def select_percentage(self, percentage):
        # calculates how many messages are needed to reach target percentage
        m_needed = self.num_messages * int(percentage) / 100
        m_so_far = 0
        for user in self.Users:
            if m_so_far < m_needed:
                m_so_far += user.num_messages
                user.selected = True
            else:
                user.selected = False
        self.find_edge_messages()

    def create_dict(self, words):
        for user in tqdm(self.Users):
            if user.selected:
                for file in user.Files:
                    for i in range(file.Meta.num_messages):
                        if "content" in file.messages[i]:
                            message = (convert(file.messages[i]["content"])).split(" ")
                            for word in message:
                                if len(word) > 1 and len(word) < 20:
                                    if word in words:
                                        words[word] += 1
                                    else:
                                        words[word] = 1

    def find_edge_messages(self):
        print("Finding oldes and newest message...")
        self.Info.oldest_timestamp = self.Users[0].Files[0].messages[0]["timestamp_ms"]
        for user in self.Users:
            if user.selected:
                for file in user.Files:
                    for i in range(file.Meta.num_messages):
                        if "timestamp_ms" in file.messages[i]:
                            ms = file.messages[i]["timestamp_ms"]
                            if self.Info.oldest_timestamp > ms:
                                self.Info.oldest_timestamp = ms
                            if self.Info.newest_timestamp < ms:
                                self.Info.newest_timestamp = ms
        self.Info.period = self.Info.newest_timestamp - self.Info.oldest_timestamp

    def graph(self):
        print("Counting messages...")
        for user in tqdm(self.Users):
            if user.selected:
                for file in user.Files:
                    for i in range(file.Meta.num_messages):
                        if "timestamp_ms" in file.messages[i]:
                            ms = file.messages[i]["timestamp_ms"]
                            

class Menu:
    def stats():
        print("")
        o = print_numbered_menu(["Brief", "With participants", "With participants and meta info"])
        print("")
        if o >= 1 and o <= 3:
            chats.print_stats()
            chats.print_times()
            if o >= 2:
                print("")
                for user in chats.Users:
                    print(user.name + ": " + str(user.num_messages) + " in " + str(len(user.Files)) 
                        + " files, selected: " + str(user.selected))
                    if o == 3:
                        for file in user.Files:
                            print(file.Meta.participants, file.Meta.num_messages)
                            print("Meta:")
                            file.Meta.print()
                        print("")

    def output():
        if chats.Info.output_name == "":
            print("Output file name not specified")
            print("Graph output will be saved as .csv and words as .txt under the same name")
            chats.Info.output_name = input("Enter the name: ")
        else:
            print("Output file name:", chats.Info.output_name)
    
    def select():
        chats.order()
        chats.print_stats()
        while True:
            print("")
            chats.select_percentage(input("Input percentage of users to be selected: "))
            chats.print_stats()
            print("")
            if ask_continue():
                break

    def most_used_words():
        print("")
        o = print_numbered_menu(["All chats", "Only selected"])
        if o == 1:
            chats.select_percentage(100)
            chats.print_stats()
        elif o == 2:
            Menu.select()

        print("Scrubbing the words...")
        words = {}
        chats.create_dict(words)

        print("There are " + str(len(words)) + " words")
        limit = int(input("Type \"0\" to save all or specify the ammount: "))
        if limit == 0: limit = len(words)

        print("Sorting the words...")
        words_sorted = {}
        for i in tqdm(range(limit)):
            max = 0
            max_key = ""
            for word in words:
                if max < words[word]:
                    max = words[word]
                    max_key = word
            words.pop(max_key)
            words_sorted[max_key] = max
        
        Menu.output()
        print("Writing " + str(len(words_sorted)) + " words to a file")
        path = args.path_out + chats.Info.output_name + "/"
        check_output_folder(path)
        with open(path + chats.Info.output_name + ".txt", "w") as file_out:
            i = 0
            for word in words_sorted:
                i += 1
                file_out.write(str(i) + ". " + str(word) + ": " + str(words_sorted[word]) + "\n")

    def

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze data downloaded from facebook')
    parser.add_argument('-i', dest='path_in', required=True, default='', help='Path to the inbox folder')
    parser.add_argument('-o', dest='path_out', required=False, default='', help='Path to the output folder')

    args = parser.parse_args()

    if args.path_out == "":
        args.path_out = args.path_in[0:args.path_in.index("/messages") + 1]
        print("Path out set to:", args.path_out)

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

                # ignore groups (yes, sometimes there are "groups" with just two participants)
                if data["thread_type"] == "Regular" and len(data["participants"]) == 2:
                    total_messages += num_messages

                    # check whether the user is already in the users array
                    check = check_existing(users, user_name)
                    meta_info = Meta(data["participants"], num_messages, file_name)
                    file = File(meta_info, messages)
                    if (check == -1):
                        # add new user
                        users.append(User(user_name, [file], num_messages))
                    else:
                        # add another file (thanks fb) to the existing user
                        users[check].Files.append(file)
                        users[check].num_messages += num_messages
                else:
                    skipped_chats += 1
                    skipped_messages += num_messages

    info = Info(skipped_messages, skipped_chats)
    chats = Analyze(users, total_messages, info)

    # second participant should always be the sender (should be the same across all files)
    chats.check_sender_name()

    chats.print_times()
    chats.print_stats()

    while True:
        print("")
        option = print_numbered_menu(["Count messages per timeframe",
         "Compile a list of most used words", "Print stats", "Order and select users", "Exit"])
        if option == 1:
            pass

        elif option == 2:
            Menu.most_used_words()

        elif option == 3:
            Menu.stats()
            
        elif option == 4:
            Menu.select()

        else:
            abort()




