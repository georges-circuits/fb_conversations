import json, os, glob
from datetime import datetime

class Inbox:

    # creates the entire structure and performes some basic sorting and analysis
    def __init__(self, path):

        self.chats = []
        files = 0
        for entry in os.listdir(path):
            file_path = os.path.join(path, entry)
            if os.path.isdir(file_path):
                # I wanted to make it into a dict but there is a problem 
                # with chat groups in terms of naming... so a list it is
                self.chats.append(Chat(file_path))
                files += 1
        
        par = []
        tot = 0
        for chat in self.chats:
            par.append(chat.meta.participants)
            tot += chat.meta.num_messages
        
        self.meta = Meta(par, tot, 0, 0, files, path)
        self.ordered = False
        self.selected_count = 0
        self.selected_messages_count = 0

        self.select_based_on_percentage(100)

    def get_stats(self):
        reg = self.count_chats_and_messages_for_type("Regular")
        reg_sel = self.count_chats_and_messages_for_type("Regular", True)
        grp = self.count_chats_and_messages_for_type("RegularGroup")
        grp_sel = self.count_chats_and_messages_for_type("RegularGroup", True)
        oth = self.count_chats_and_messages_for_type("other")
        oth_sel = self.count_chats_and_messages_for_type("other", True)
        return (
            f'Stats:\n'
            f'Number of chats loaded: {self.meta.files_count} ({self.selected_count} selected)\n'
            f'Loaded messages: {self.meta.num_messages} ({self.selected_messages_count} selected)\n'
            f'Average messages per conversation: {int(self.meta.num_messages / self.meta.files_count)} ({int(self.selected_messages_count / self.selected_count)} in selected chats)\n'
            f'Currently selected {round(self.selected_count / self.meta.files_count * 100, 2)} % of chats ({round(self.selected_messages_count / self.meta.num_messages * 100, 2)} % of messages) - Selected/Loaded:\n' 
            f'Regular chats: {reg_sel[1]}/{reg[1]} messages ({reg_sel[0]}/{reg[0]} chats)\n'
            f'Group chats: {grp_sel[1]}/{grp[1]} messages ({grp_sel[0]}/{grp[0]} group chats)\n'
            f'Other: {oth_sel[1]}/{oth[1]} messages ({oth_sel[0]}/{oth[0]} chats)\n'
        )
    
    def get_times(self):
        return (
            f'Time stats in selected (UTC):\n'
            f'Oldest message: {convert_ms(self.meta.oldest_timestamp)}\n'
            f'Newest message: {convert_ms(self.meta.newest_timestamp)}\n'
            f'Which totals a period of {convert_ms_year(self.meta.period)} years\n'
        )

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
        self._calculate_stats_in_selected()

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
        if self.meta.files_count > 1:
            while not sorted:
                sorted = True
                for i in range((self.meta.files_count) - 1):
                    if self.chats[i].meta.num_messages < self.chats[i + 1].meta.num_messages:
                        sorted = False
                        already_sorted = False
                        self.chats[i], self.chats[i + 1] = self.chats[i + 1], self.chats[i]
        self.ordered = True
        for i in range(self.meta.files_count):
            self.chats[i].index = i + 1
            self.chats[i].index_verbose = f'Chat{i + 1}'
        if already_sorted:
            print("Already ordered")

    def _calculate_stats_in_selected(self):
        self.selected_count = 0
        self.selected_messages_count = 0
        for chat in self.get_selected():
            self.selected_count += 1
            self.selected_messages_count += chat.meta.num_messages

    # chat_type: "Regular", "RegularGroup", "other", "all"
    # returns tuple (chats_count, messages_count)
    def count_chats_and_messages_for_type(self, chat_type, only_in_selected = False):
        chats_count = 0
        messages_count = 0
        for chat in self.chats:
            if not only_in_selected or (only_in_selected and chat.is_selected()):
                if "all" == chat_type or ("other" != chat_type and chat_type == chat.type) or ("other" == chat_type and not "Regular" in chat.type):
                    chats_count += 1
                    messages_count += chat.meta.num_messages
        return (chats_count, messages_count)

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
        self.type = ''
        self.messages = None
        self.selected = True
        
        # indexes are assigned by Inbox._order() and start from 1
        self.index = -1
        self.index_verbose = ""

        files = 0
        for file_name in glob.glob(os.path.join(path_to_inbox, "*.json")):
            with open(file_name, "r") as json_file:
                data = json.load(json_file, object_hook=_parse_obj)

            if self.messages == None:
                self.messages = data["messages"]
            else:
                #self.messages.append(data["messages"])
                self.messages += data["messages"]
            files += 1
            
            if self.name == '':
                p = len(data["participants"])
                if p == 2:
                    self.name = data["participants"][0]["name"]
                elif p < 2:
                    self.name = data["title"]
                elif p > 2:
                    self.name = data["title"]
                pass
            self.type = data["thread_type"]
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
        
        # just so I don't have to use the "name" keyword
        par = []
        for p in participants:
            par.append(p["name"])
        
        self.meta = Meta(par, len(self.messages), oldest_timestamp, newest_timestamp, files, path_to_inbox)
            
    def is_selected(self):
        return self.selected
    
    def get_stats(self):
        return (
            f'Messages: {self.meta.num_messages}\n'
            f'First-last message: {convert_ms_year(self.meta.period)} years\n'
            f'Messages per day: {round(self.meta.num_messages / (self.meta.period / 1000 / 3600 / 24), 2)}\n'
            f'Oldest message: {convert_ms(self.meta.oldest_timestamp)}\n'
            f'Newest message: {convert_ms(self.meta.newest_timestamp)}\n'
            f'Chat type: {self.type}\n'
        )
    
    def get_debug(self):
        return (
            f'name: {self.name}\n'
            f'type: {self.type}\n'
            f'selected: {self.selected}\n'
            f'index: {self.index}\n'
            f'{self.meta.get_debug()}'
        )

class Meta:

    def __init__(self, participants, num_messages, oldest_timestamp, newest_timestamp, files_count, path):
        self.participants = participants
        self.num_messages = num_messages
        self.oldest_timestamp = oldest_timestamp
        self.newest_timestamp = newest_timestamp
        self.period = self.newest_timestamp - self.oldest_timestamp
        self.path = path
        self.files_count = files_count
    
    def get_debug(self):
        return (
            f'participants: {str(self.participants)}\n'
            f'num_messages: {self.num_messages}\n'
            f'oldest_timestamp: {self.oldest_timestamp}\n'
            f'newest_timestamp: {self.newest_timestamp}\n'
            f'period: {self.period}\n'
            f'files_count: {self.files_count}\n'
            f'path: {self.path}\n'
        )


def convert_ms(value_ms):
    return datetime.utcfromtimestamp(value_ms / 1000).strftime('%d.%m.%Y %H:%M:%S')

def convert_ms_year(value_ms):
    return round(value_ms / 1000 / 3600 / 24 / 365.25, 2)

def convert(s):
    chars_f = ['á', 'ď', 'í', 'č', 'ť', 'ó', 'ő', 'ö', 'ú', 'ů', 'ř', 'ň', 'é', 'ý', 'ě', 'š', 'ž', 'Ě', 'Š', 'Č', 'Ř', 'Ž', 'Ý', 'Á', 'Í', 'É', 'Ť', 'Ď', 'Ú', 'Ů', 'Ň']
    chars_t = ['a', 'd', 'i', 'c', 't', 'o', 'o', 'o', 'u', 'u', 'r', 'n', 'e', 'y', 'e', 's', 'z', 'E', 'S', 'C', 'R', 'Z', 'Y', 'A', 'I', 'E', 'T', 'D', 'U', 'U', 'N']
    for i in range(len(chars_f)):
        s = s.replace(chars_f[i], chars_t[i])
    return s