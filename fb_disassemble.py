import json, os, glob
#from tqdm import tqdm

class Inbox:
    
    # creates the entire structure and performes some basic sorting and analysis
    def __init__(self, path):

        chats = []
        for entry in os.listdir(path):
            file_path = os.path.join(path, entry)
            if os.path.isdir(file_path):
                # I wanted to make it into a dict but there is a problem 
                # with chat groups in terms of naming... so a list it is
                chats.append(Chat(file_path))
        self.chats = chats
        
        par = []
        tot = 0
        for chat in self.chats:
            par.append(chat.meta.participants)
            tot += chat.meta.num_messages
        
        self.meta = Meta(par, tot, 0, 0, path)
        self.ordered = False
        self.total_count = len(chats)

        self.select_based_on_percentage(100)

    def select_based_on_percentage(self, percentage):
        self._order()
        # calculates how many messages are needed to reach target percentage
        m_needed = self.meta.num_messages * int(percentage) / 100
        m_so_far = 0
        
        for user in self.chats:
            if m_so_far < m_needed:
                m_so_far += user.meta.num_messages
                user.selected = True
            else:
                user.selected = False
        self._find_edge_messages_in_selected()

    def _find_edge_messages_in_selected(self):
        print("Finding oldest and newest message...")
        self.meta.oldest_timestamp = 10 ** 20
        for chat in self.get_selected():
            if self.meta.oldest_timestamp > chat.meta.oldest_timestamp:
                self.meta.oldest_timestamp = chat.meta.oldest_timestamp
            if self.meta.newest_timestamp < chat.meta.newest_timestamp:
                self.meta.newest_timestamp = chat.meta.newest_timestamp
        self.meta.period = self.meta.newest_timestamp - self.meta.oldest_timestamp

    def _order(self):
        sorted = False
        already_sorted = True
        print ("Ordering chats based on ammount of messages...")
        if self.total_count > 1:
            while not sorted:
                sorted = True
                for i in range((self.total_count) - 1):
                    if self.chats[i].meta.num_messages < self.chats[i + 1].meta.num_messages:
                        sorted = False
                        already_sorted = False
                        self.chats[i], self.chats[i + 1] = self.chats[i + 1], self.chats[i]
        self.ordered = True
        for i in range(self.total_count):
            self.chats[i].index = i
        if already_sorted:
            print("Already ordered")

    def count_messages_in_selected(self):
        total = 0
        for chat in self.get_selected():
            total += chat.meta.num_messages
        return total

    def get_selected(self):
        for chat in self.chats:
            if chat.is_selected():
                yield chat

class Chat:

    def __init__(self, path_to_inbox):

        def _parse_obj(obj):
            # courtesy of StackOverflow (fixes the cursed character encoding) 
            # this is updated because the previous solution (fix_mojibake_escapes)
            # stopped working with newer downloads... this one is even more comlicated
            # https://stackoverflow.com/questions/50008296/facebook-json-badly-encoded?rq=1
            for key in obj:
                if isinstance(obj[key], str):
                    obj[key] = obj[key].encode('latin_1').decode('utf-8')
                elif isinstance(obj[key], list):
                    obj[key] = list(map(lambda x: x if type(x) != str else x.encode('latin_1').decode('utf-8'), obj[key]))
                pass
            return obj

        self.name = ''
        self.messages = None
        self.selected = True
        self.index = -1

        for file_name in glob.glob(os.path.join(path_to_inbox, "*.json")):
            with open(file_name, "r") as json_file:
                data = json.load(json_file, object_hook=_parse_obj)

            if self.messages == None:
                self.messages = data["messages"]
            else:
                self.messages.append(data["messages"])
            
            #TODO: has to check whether the name is the same for every file
            if self.name == '':
                self.name = data["participants"][0]["name"]
            #TODO: same here
            participants = data["participants"]
        
        oldest_timestamp = self.messages[0]["timestamp_ms"]
        newest_timestamp = 0
        for message in self.messages:
            if "timestamp_ms" in message:
                ms = message["timestamp_ms"]
                if oldest_timestamp > ms:
                    oldest_timestamp = ms
                if newest_timestamp < ms:
                    newest_timestamp = ms
        
        # just so I do not have to use the "name" keyword
        par = []
        for p in participants:
            par.append(p["name"])
        
        self.meta = Meta(par, len(self.messages), oldest_timestamp, newest_timestamp, path_to_inbox)
            
    def is_selected(self):
        return self.selected
    
class Meta:

    def __init__(self, participants, num_messages, oldest_timestamp, newest_timestamp, path):
        self.participants = participants
        self.num_messages = num_messages
        self.oldest_timestamp = oldest_timestamp
        self.newest_timestamp = newest_timestamp
        self.period = self.newest_timestamp - self.oldest_timestamp
        self.path = path
    
    def info(self):
        return f'participants: {str(self.participants)}\nnum_messages: {self.num_messages}\npath: {self.path}\n'


"""
    def get_overall_statistics(self):

        selected = 0
        selected_messages = 0
        for user in self.Users: 
            if user.selected: 
                selected += 1
                selected_messages += user.num_messages
        
        out = f"Number of chats loaded: {len(self.chats)} ({selected} selected)\n"
        out += f"Loaded messages: " + {str(self.num_messages)} + " (" + {str(selected_messages)} + " selected)" + "\n"
        out += f"Messages total: " + {str(self.num_messages + self.Info.skipped_messages)} + " (including " + {str(self.Info.skipped_messages)} + " in groups - not loaded)" + "\n"
        out += f"Currently selected " + str(round(selected / len(self.Users) * 100, 2)) + "% of chats (" + {str(round(selected_messages / self.num_messages * 100, 2))} + "% of messages)" + "\n"
        out += f"Average per conversation:{str(int(self.num_messages / len(self.Users)))} ({str(int(selected_messages / selected))} in selected chats)\n"

    def print_times(self, to_str = False):
        if self.Info.period == 0:
            self.find_edge_messages()
        s = "\nTime stats (UTC):\n"
        s += "Oldest message: " + str(convert_ms(self.Info.oldest_timestamp)) + "\n"
        s += "Newest message: " + str(convert_ms(self.Info.newest_timestamp)) + "\n"
        s += "Which totals a period of " + str(convert_ms_year(self.Info.period)) + " years\n"
        if to_str:
            return s
        print(s, end="")
"""