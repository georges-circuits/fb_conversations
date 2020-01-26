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

def parse_obj(obj):
    for key in obj:
        if isinstance(obj[key], str):
            obj[key] = obj[key].encode('latin_1').decode('utf-8')
        elif isinstance(obj[key], list):
            obj[key] = list(map(lambda x: x if type(x) != str else x.encode('latin_1').decode('utf-8'), obj[key]))
        pass
    return obj

def ask_continue():
    print("Continue? [Y/n] ", end='')
    resp = input().lower()
    if "n" in resp:
        return False
    return True

def ask_yes_no():
    print("[Y/n] ", end='')
    resp = input().lower()
    if "n" in resp:
        return False
    return True

def convert(s):
    chars_f = ['á', 'ď', 'í', 'č', 'ť', 'ó', 'ő', 'ö', 'ú', 'ů', 'ř', 'ň', 'é', 'ý', 'ě', 'š', 'ž', 'Ě', 'Š', 'Č', 'Ř', 'Ž', 'Ý', 'Á', 'Í', 'É', 'Ť', 'Ď', 'Ú', 'Ů', 'Ň']
    chars_t = ['a', 'd', 'i', 'c', 't', 'o', 'o', 'o', 'u', 'u', 'r', 'n', 'e', 'y', 'e', 's', 'z', 'E', 'S', 'C', 'R', 'Z', 'Y', 'A', 'I', 'E', 'T', 'D', 'U', 'U', 'N']
    for i in range(len(chars_f)):
        s = s.replace(chars_f[i], chars_t[i])
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

def chceck_output_file(path):
    with open(path, "w") as file_out:
        pass
    print("File created")

def check_existing(users, name):
    for i in range(len(users)):
        if name == users[i].name:
            return i
    return -1

def create_log():
    print ("Creating log file...")
    with open("log.txt", "w") as log:
        pass

def log(line):
    with open("log.txt", "a") as log:
        log.write(line + "\n")


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
        self.index = ""

class Info:
    def __init__(self, skipped_messages, skipped_chats):
        self.skipped_messages = skipped_messages
        self.skipped_chats = skipped_chats
        self.output_name = ""
        self.oldest_timestamp = 0
        self.newest_timestamp = 0
        self.period = 0
        self.anonymize = False

class Analyze:
    def __init__(self, Users, num_messages, Info, ordered = False):
        self.Users = Users
        self.ordered = ordered
        self.num_messages = num_messages
        self.Info = Info


    def order(self):
        sorted = False
        already_sorted = True
        print ("Ordering chats based on ammount of messages...")
        if len(self.Users) > 1:
            while not sorted:
                sorted = True
                for i in range(len(self.Users) - 1):
                    if self.Users[i].num_messages < self.Users[i + 1].num_messages:
                        sorted = False
                        already_sorted = False
                        self.Users[i], self.Users[i + 1] = self.Users[i + 1], self.Users[i]
        self.ordered = True
        for i in range(len(self.Users)):
            self.Users[i].index = "User" + str(i + 1)
        if already_sorted:
            print("Already sorted")

    def print_stats(self, to_str = False):
        s = "\nStats:\n"
        selected = 0
        selected_messages = 0
        for user in self.Users: 
            if user.selected: 
                selected += 1
                selected_messages += user.num_messages
        s += "Number of chats loaded: " + str(len(self.Users)) + " (" + str(selected) + " selected)" + "\n"
        s += "Loaded messages: " + str(self.num_messages) + " (" + str(selected_messages) + " selected)" + "\n"
        s += "Messages total: " + str(self.num_messages + self.Info.skipped_messages) + " (including " + str(self.Info.skipped_messages) + " in groups - not loaded)" + "\n"
        s += "Currently selected " + str(round(selected / len(self.Users) * 100, 2)) + "% of chats (" + str(round(selected_messages / self.num_messages * 100, 2)) + "% of messages)" + "\n"
        if to_str:
            return s
        print(s, end="")

    def print_times(self, to_str = False):
        if self.Info.period == 0:
            self.find_edge_messages()
        s = "\nTime stats (UTC):\n"
        s += "Oldest message: " + str(convert_ms(self.Info.oldest_timestamp)) + "\n"
        s += "Newest message: " + str(convert_ms(self.Info.newest_timestamp)) + "\n"
        s += "Which totals a period of " + str(round(self.Info.period / 1000 / 3600 / 24 / 365.25, 2)) + " years\n"
        if to_str:
            return s
        print(s, end="")

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

    def find_edge_messages(self):
        print("Finding oldest and newest message...")
        # cannot be zore of course
        self.Info.oldest_timestamp = self.Users[0].Files[0].messages[0]["timestamp_ms"]
        for user in self.Users:
            if user.selected:
                for file in user.Files:
                    for message in file.messages:
                        if "timestamp_ms" in message:
                            ms = message["timestamp_ms"]
                            if self.Info.oldest_timestamp > ms:
                                self.Info.oldest_timestamp = ms
                            if self.Info.newest_timestamp < ms:
                                self.Info.newest_timestamp = ms
        self.Info.period = self.Info.newest_timestamp - self.Info.oldest_timestamp

    def create_dict(self, words):
        for user in tqdm(self.Users):
            if user.selected:
                for file in user.Files:
                    for i in range(file.Meta.num_messages):
                        if "content" in file.messages[i]:
                            message = (convert(file.messages[i]["content"].lower())).split(" ")
                            for word in message:
                                if len(word) > 1 and len(word) < 20:
                                    if word in words:
                                        words[word] += 1
                                    else:
                                        words[word] = 1

    def graph(self, names_vals, period, periods_count):
        print("Counting messages...")
        # go through all users...
        for user in tqdm(self.Users):
            if user.selected:
                
                # add only selected users to the dictionary
                if self.Info.anonymize:
                    names_vals[user.index] = []
                    for i in range(periods_count - 1):
                        names_vals[user.index].append(0)
                else:
                    names_vals[user.name] = []
                    for i in range(periods_count - 1):
                        names_vals[user.name].append(0)
                
                # ...all user files...
                for file in user.Files:
                    # ... and the entire periods_count and count the number of messages per each period
                    for period_num in range(periods_count - 1):
                        
                        lowest = self.Info.oldest_timestamp + (period_num * period)
                        highest = self.Info.oldest_timestamp + ((period_num + 1) * period)
                        
                        for i in range(file.Meta.num_messages):
                            if "timestamp_ms" in file.messages[i]:
                                ms = file.messages[i]["timestamp_ms"]
                                if ms >= lowest and ms < highest:
                                    if self.Info.anonymize:
                                        names_vals[user.index][period_num] += 1
                                    else:
                                        names_vals[user.name][period_num] += 1
                            else:
                                log("timestamp_ms not found: " + user.name + ", message: " + str(i))
        # add "combined" to the dict
        combined = []
        for i in range(periods_count - 1):
            sum = 0
            for name in names_vals:
                sum += names_vals[name][i]
            combined.append(sum)
        names_vals["combined"] = combined

        # add "date" key as the last line
        names_vals["date"] = []
        for period_num in range(periods_count - 1):
            # cut just the date
            date = (convert_ms(self.Info.oldest_timestamp + (period_num * period)))[0:10]
            names_vals["date"].append(date)



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
                    print(user.name + " (" + user.index + "): " + str(user.num_messages) + " in " + str(len(user.Files)) 
                        + " files, selected: " + str(user.selected))
                    if o == 3:
                        for file in user.Files:
                            print(file.Meta.participants, file.Meta.num_messages)
                            print("Meta:")
                            file.Meta.print()
                        print("")

    def ask_anonymize():
        print("Anonymize the data? ", end="")
        chats.Info.anonymize = ask_yes_no()

    def output():
        if chats.Info.output_name == "":
            print("\nOutput file name not specified")
            print("Graph output will be saved as .csv and words as .txt under the same name")
            if chats.Info.anonymize: print ("Anonymize is enabled, _anon will be added to the name")
            chats.Info.output_name = input("Enter the name: ")
            if chats.Info.anonymize: chats.Info.output_name += "_anon"
        else:
            print("Output file name:", chats.Info.output_name)
    
    def select(pre = 0):
        chats.order()
        chats.print_stats()
        while True:
            print("")
            # the allows pre to be used but also requires the confirmation and enables changes
            if pre == 0:
                val = input("Input percentage of users to be selected: ")
            else:
                print ("Applying predefined value:", pre)
                val = pre
                pre = 0
            chats.select_percentage(val)
            chats.print_stats()
            print("")
            if ask_continue():
                break

    def most_used_words(pre = False, limit = 0):
        print("")
        print("Output path:", args.path_out)
        Menu.output()
        path = args.path_out + chats.Info.output_name + "/"
        check_output_folder(path)
        chceck_output_file(path + chats.Info.output_name + ".txt")

        if pre:
            print("Predefined to select all messages")
            o = 1
        else:
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
        if limit == 0: 
            limit = int(input("Type \"0\" to save all or specify the ammount: "))
        else:
            print("Predefined limit value:", limit)
        if limit == 0 or limit > len(words): limit = len(words)

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
        
        print("Writing " + str(len(words_sorted)) + " words to the file")
        with open(path + chats.Info.output_name + ".txt", "w") as file_out:
            i = 0
            for word in words_sorted:
                i += 1
                file_out.write(str(i) + ". " + str(word) + ": " + str(words_sorted[word]) + "\n")

    def graph(period = 0, select = 0):
        if select == 0:
            Menu.select()
        else:
            Menu.select(select)
        
        print("Output path:", args.path_out)
        Menu.output()
        path = args.path_out + chats.Info.output_name + "/"
        check_output_folder(path)
        chceck_output_file(path + chats.Info.output_name + ".csv")

        if period == 0:
            period = int(input("Enter the number of days for a window: ")) * 24 * 3600 * 1000
        else:
            print("Applying predefined period value:", period)
            period = period * 24 * 3600 * 1000
        periods_count = int(chats.Info.period / period) + 1
        print(round(chats.Info.period / 1000 / 3600 / 24 / 365.25, 2), "years split into", periods_count, "periods")

        names_vals = {}
        chats.graph(names_vals, period, periods_count)

        print("Writing data to the file...")
        with open(path + chats.Info.output_name + ".csv", "w") as file_out:
            for chat in names_vals:
                file_out.write(convert(chat) + ";")
                for val in names_vals[chat]:
                    file_out.write(str(val) + ";")
                file_out.write("\n")
    
        with open(path + chats.Info.output_name + "_meta.txt", "w") as file_out:
            file_out.write(chats.print_stats(True))
            file_out.write(chats.print_times(True))
            file_out.write("\nperiod: " + str(period / 3600000 / 24) + " days, periods: " + str(periods_count) + "\n")
            file_out.write("\nIncluded in the graph:\n")
            for user in chats.Users:
                if user.selected:
                    if chats.Info.anonymize:
                        file_out.write(user.index + ": " + str(user.num_messages) + "\n")
                    else:
                        file_out.write(user.name + ": " + str(user.num_messages) + "\n")

            if not chats.Info.anonymize:
                file_out.write("\nNot included in the graph:\n")
                for user in chats.Users:
                    if not user.selected:
                        file_out.write(user.name + ": " + str(user.num_messages) + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze data downloaded from facebook')
    parser.add_argument('-i', dest='path_in', required=True, default='', help='Path to the inbox folder')
    parser.add_argument('-o', dest='path_out', required=False, default='', help='Path to the output folder')

    args = parser.parse_args()

    if args.path_out == "":
        args.path_out = args.path_in[0:args.path_in.index("/messages") + 1]
        print("Path out set to:", args.path_out)

    create_log()

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
                # this is updated because the previous solution (fix_mojibake_escapes)
                # stopped working with newer downloads... this one is even more comlicated
                # https://stackoverflow.com/questions/50008296/facebook-json-badly-encoded?rq=1
                with open(file_name, "r") as json_file:
                    data = json.load(json_file, object_hook=parse_obj)

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
        else:
            log(file_path + " is not dir")

    info = Info(skipped_messages, skipped_chats)
    chats = Analyze(users, total_messages, info)

    # second participant should always be the sender (should be the same across all files)
    chats.check_sender_name()

    chats.print_times()
    chats.print_stats()

    while True:
        print("")
        option = print_numbered_menu(["Predefined", "Count messages per timeframe",
         "Compile a list of most used words", "Print stats", "Order and select users",
         "Anonymize setting", "Exit"])
        
        if option == 1:
            Menu.ask_anonymize()
            Menu.graph(period = 7, select = 85)
            Menu.most_used_words(pre = True, limit = 5000)

        elif option == 2:
            Menu.graph()

        elif option == 3:
            Menu.most_used_words()

        elif option == 4:
            Menu.stats()
            
        elif option == 5:
            Menu.select()

        elif option == 6:
            Menu.ask_anonymize()

        else:
            abort()




