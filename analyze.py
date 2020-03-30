import argparse, os, sys, signal
import fb_disassemble as fb
from tqdm import tqdm


class UI:
    def __init__(self, diags, analyze):
        self.diags = diags
        self.analyze = analyze

    def graph(self, inbox):
        self.diags.output_file_name_set()

        out_path = os.path.join(self.diags.output_path, self.diags.output_file_name)
        self.diags.create_output_folder(out_path)

        csv_path = os.path.join(out_path, self.diags.output_file_name + ".csv")
        meta_path = os.path.join(out_path, self.diags.output_file_name + "_meta.txt")
        if not self.diags.check_output_file(csv_path): return
        if not self.diags.check_output_file(meta_path): return
        print()

        options = [
            ("Select chats", (self.diags.select_chats, inbox)),
            ("Leave the current selection", (self.diags.print_stats_and_times, inbox)),
        ]
        print()
        if self.diags.print_numbered_menu_and_execute(options, True):
            return
        
        period = int(input("Enter the number of days for a window: "))
        period = period * 24 * 3600 * 1000

        self.analyze.save_graph(inbox, period, csv_path, meta_path)

    def words(self, inbox):
        self.diags.output_file_name_set()

        out_path = os.path.join(self.diags.output_path, self.diags.output_file_name)
        self.diags.create_output_folder(out_path)

        list_path = os.path.join(out_path, self.diags.output_file_name + "_words.txt")
        if not self.diags.check_output_file(list_path): return

        selected_names = []
        options = [
            ("All chats", [(inbox.select_chats, 100), (self.diags.print_stats_and_times, inbox)]),
            ("Only selected chats", (self.diags.select_chats, inbox)),
            ("Leave the current selection", (self.diags.print_stats_and_times, inbox)),
            ("Only the sender (uses the current selection)", (selected_names.append, inbox.chats[0].meta.participants[1]))
        ]
        print()
        if self.diags.print_numbered_menu_and_execute(options, True):
            return
                
        self.analyze.save_most_used(inbox, selected_names, list_path)

class Dialogs:
    def __init__(self):
        self.output_file_name = ""
        self.output_path = ""
        self.anonymize = False

    
    # LIBRARY QUERIES
    def select_chats(self, inbox):
        self.print_stats_and_times(inbox)
        while True:
            print("Chose which chats to focus on")
            options = [
                ("All", "all"),
                ("Just regular", "regular"),
                ("Just groups", "group"),
                ("All other than regular and groups", "other")
            ]
            chat_type = self.print_numbered_menu_return_result(options)

            # TODO: so it won't crash when you misstype
            percent = input("Input percentage of messages to be selected (leave blank for all): ")
            if percent:
                percent = int(percent)
            else:
                percent = 100
            
            inbox.select_chats(percent, chat_type)
            print()
            self.print_stats_and_times(inbox)
            if self.ask_Y_n("Continue?"):
                break         
    
    def print_stats_and_times(self, inbox):
        print(inbox.get_stats())
        print(inbox.get_times())
    
    def print_numbered_menu(self, menu):
        while True:
            i = 0
            for item in menu:
                i += 1
                print(f'{i}. {item}')
            if i == 1:
                print("Chose 1: ", end="")
            else:
                print(f"Chose 1 to {i}: ", end="")
            u_in = input()
            if u_in.isdigit():
                u_in = int(u_in)
                if u_in >= 1 and u_in <= i:
                    return u_in
                else:
                    print("\nInput must be within the said range")
            else:
                print("\nOnly digits allowed")
    
    def print_numbered_menu_return_result(self, methods):
        menu = []
        for method in methods:
            menu.append(method[0])
        return methods[self.print_numbered_menu(menu) - 1][1]

    def print_numbered_menu_and_execute(self, methods, include_back = False):
        if include_back:
            methods.append(("Go back", "__back"))
        output = self.print_numbered_menu_return_result(methods)
        print()
        if include_back and "__back" in output:
            return True
        if isinstance(output, list):
            for out in output:
                if isinstance(out, tuple):
                    out[0](out[1])
                else:
                    out()
        else:
            out = output
            if isinstance(out, tuple):
                out[0](out[1])
            else:
                out()
    
    def ask_anonymize(self):
        print(f"Current setting: {self.anonymize}")
        self.anonymize = self.ask_Y_n("Anonymize the data?")
        self.check_output_file_name_anon()
    

    # FILE HANDLING
    def output_file_name_set(self):
        if self.output_file_name == "":
            print("Output file name not yet specified")
            self.output_file_name = input("Enter output file name (without extension): ")
        else:
            print(f'Current output file name is: {self.output_file_name}')
            if not self.ask_Y_n("Do you want to keep it?"):
                self.output_file_name = input("Enter output file name (without extension): ")
        self.check_output_file_name_anon()
    
    def check_output_file_name_anon(self):
        anon_designator = "_anon"
        
        if self.output_file_name:
            if self.anonymize and not anon_designator in self.output_file_name:
                self.output_file_name += anon_designator
                print(f"{anon_designator} added to the file name")
            
            if not self.anonymize and anon_designator in self.output_file_name:
                self.output_file_name.replace(anon_designator, "")
                print(f"{anon_designator} removed from the file name")
    
    def create_output_folder(self, path):
        if not os.access(path, os.F_OK):
            os.mkdir(path)
            print("Created folder", end=" ")
        else: 
            print("Using existing output folder", end=" ")
        print(path + '/')

    def check_output_file(self, path, force = False):
        if os.path.isfile(path):
            if not force and not self.ask_Y_n(f'File {self.cut_file_name(path)} already exist. Overwrite?'):
                return False
        with open(path, "w") as _:
            pass
        print(f"File {self.cut_file_name(path)} created")
        return True
    
    def cut_file_name(self, path):
        return path[path.rindex("/") + 1:]
    
    
    def abort(self):
        print("Aborting")
        sys.exit()

    def ask_Y_n(self, message = ""):
        print(f"{message} [Y/n] ", end='')
        resp = input().lower()
        if "n" in resp:
            return False
        return True

class Analyze:
    def __init__(self, diags):
        self.diags = diags

    def predefined_analyze(self, inbox): 
        # Enter the number of days for a window:
        period = 30
        # Chat selection:
        percentage = 80
        chat_type = "all"

        print(f"Running in predefined mode!\nperiod: {period}, percentage: {percentage}, chat_type: {chat_type}")      
        # only thing that the user needs to set
        self.diags.output_file_name_set()

        out_path = os.path.join(self.diags.output_path, self.diags.output_file_name)
        self.diags.create_output_folder(out_path)

        csv_path = os.path.join(out_path, self.diags.output_file_name + ".csv")
        meta_path = os.path.join(out_path, self.diags.output_file_name + "_meta.txt")
        list_path = os.path.join(out_path, self.diags.output_file_name + "_words.txt")
        self.diags.check_output_file(csv_path, True)
        self.diags.check_output_file(meta_path, True)
        self.diags.check_output_file(list_path, True)
        print()
        
        inbox.select_chats(percentage, chat_type)      
        period = period * 24 * 3600 * 1000
        self.save_graph(inbox, period, csv_path, meta_path)

        """ inbox.select_chats(100, "regular")
        selected_names = [inbox.chats[0].meta.participants[1]]
        self.save_most_used(inbox, selected_names, list_path) """

    def save_graph(self, inbox, period, csv_path, meta_path):
        periods_count = int(inbox.meta.period / period) + 1
        periods_meta = f'{fb.convert_ms_year(inbox.meta.period)} years split into {periods_count} periods'
        print(periods_meta)

        print("Counting messages...\n")
        names_vals = {}

        date_list = []
        for i in range(periods_count - 1):
            date = (fb.convert_ms(inbox.meta.oldest_timestamp + (i * period)))[0:10]
            date_list.append(date)
        names_vals["date"] = date_list

        # go through all chats...
        for chat in inbox.get_selected():          
            # initiate the dictionary
            key = chat.index_verbose if self.diags.anonymize else chat.name
            names_vals[key] = []
            for i in range(periods_count - 1):
                names_vals[key].append(0)
            
            # ...and the entire periods_count and count the number of messages per each period
            for period_num in range(periods_count - 1):
                
                lowest = inbox.meta.oldest_timestamp + (period_num * period)
                highest = inbox.meta.oldest_timestamp + ((period_num + 1) * period)
                
                for message in chat.messages:
                    if "timestamp_ms" in message:
                        ms = message["timestamp_ms"]
                        if ms >= lowest and ms < highest:
                            names_vals[key][period_num] += 1
        
        
        combined = []
        for i in range(periods_count - 1):
            sum = 0
            for name in names_vals:
                if not name == "date":
                    sum += names_vals[name][i]
            combined.append(sum)
            #FIXME: (make nicer) cut just the date
            #date = (fb.convert_ms(inbox.meta.oldest_timestamp + (i * period)))[0:10]
            #date_list.append(date)
        # add "combined" to the dict, add "date" key as the last line
        names_vals["combined"] = combined
        
        print("Writing data to the file...")
        with open(csv_path, "w", encoding="utf-8") as file_out:
            for chat in names_vals:
                file_out.write(fb.remove_diacritic(chat) + ";")
                for val in names_vals[chat]:
                    file_out.write(f'{val};')
                file_out.write("\n")

        print("Writing meta info...")
        with open(meta_path, "w", encoding="utf-8") as file_out:
            file_out.write(inbox.get_stats() + "\n")
            file_out.write(inbox.get_times())
            file_out.write(f'{periods_meta} ({fb.convert_ms_to_day(period)} days per period)\n')
            
            file_out.write("\nIncluded in the graph (selected users):\n")
            for chat in inbox.get_selected():
                if self.diags.anonymize:
                    file_out.write(chat.index_verbose)
                else:
                    file_out.write(chat.name)
                file_out.write(f'\n{chat.get_stats()}\n')

    def save_most_used(self, inbox, selected_names, list_path):
        if selected_names:
            print(f"Selected participant name: {selected_names}")
        
        unwanted_chars = "?!.,"

        print("Scrubbing the words...")
        words = {}
        for chat in inbox.get_selected():
            for message in chat.messages:
                if "content" in message:
                    content = None
                    if not selected_names or (selected_names and message["sender_name"] in selected_names):
                        content = message["content"]
                    if content:
                        # all this formats the individual words so that there are as little duplicate entries as possible
                        content = fb.remove_diacritic(content.lower().translate({ord(ch): None for ch in unwanted_chars})).split(" ")
                        for word in content:
                            if len(word) > 1 and len(word) < 20:
                                if word in words:
                                    words[word] += 1
                                else:
                                    words[word] = 1

        print(f"\nThere are {len(words)} unique words")
        limit = int(input("Type \"0\" to save all or specify the ammount: "))
        if limit == 0 or limit > len(words): limit = len(words)

        print("Sorting the words...")
        words_sorted = {}
        # takes a lot of time
        #TODO: mark the first word from which there are just single word entries
        # and use that as endstop
        for i in tqdm(range(limit)):
            max = 0
            max_key = ""
            for word in words:
                if max < words[word]:
                    max = words[word]
                    max_key = word
            words.pop(max_key)
            words_sorted[max_key] = max
        
        print(f"\nWriting {len(words_sorted)} words to the file")
        with open(list_path, "w", encoding="utf-8") as file_out:
            for i, word in enumerate(words_sorted):
                file_out.write(f'{i}. {word}: {words_sorted[word]}\n')


def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Analyze data downloaded from facebook')
    parser.add_argument('-i', dest='path_in', required=True, default='', help='Path to the /inbox/ folder')
    parser.add_argument('-o', dest='path_out', required=False, default='', help='Path to the output folder')

    args = parser.parse_args()
    diags = Dialogs()

    args.path_in = os.path.normpath(args.path_in)
    if args.path_out == "":
        args.path_out = args.path_in[0:args.path_in.index("/messages") + 1]
        print("Path out set to:", args.path_out)
        if not os.access(args.path_out, os.F_OK):
            print("Failed to set the output path automatically, plese use the -o argument to se it manually")
            diags.abort()
    else:
        if not os.access(args.path_out, os.F_OK):
            print("Failed to access the output folder")
            diags.abort()

    print("Loading files...")
    inbox = fb.Inbox(args.path_in)

    diags.output_path = args.path_out
    analyze = Analyze(diags)
    ui = UI(diags, analyze)

    print()
    diags.print_stats_and_times(inbox)

    menu = [
        ("Count messages per timeframe", (ui.graph, inbox)),
        ("Compile a list of most used words", (ui.words, inbox)),
        ("Anonymize setting", diags.ask_anonymize),
        ("Select chats", (diags.select_chats, inbox)), 
        ("Print statistics", (diags.print_stats_and_times, inbox)), 
        ("Run predefined", (analyze.predefined_analyze, inbox)),
        ("Exit", diags.abort)
    ]
    while True:
        print()
        diags.print_numbered_menu_and_execute(menu)


def signal_handler(sig, frame):
    print("\n\nSIGINT received\nAborting")
    sys.exit()

if __name__ == '__main__':
    main()