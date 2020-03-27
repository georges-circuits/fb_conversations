import argparse, os, sys
import fb_disassemble as fb

class Dialogs:
    def ask_continue_Y_n(self):
        print("Continue? [Y/n] ", end='')
        resp = input().lower()
        if "n" in resp or "N" in resp:
            return False
        return True

    def select_users(self, inbox):
        self.print_stats_and_times(inbox)
        while True:
            print()
            inbox.select_based_on_percentage(int(input("Input percentage of users to be selected: ")))
            print("")
            self.print_stats_and_times(inbox)
            if self.ask_continue_Y_n():
                break
    
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
    
    def print_numbered_menu_methods(self, methods):
        menu = []
        for method in methods:
            menu.append(method[0])
        answ = self.print_numbered_menu(menu)
        output = methods[answ - 1][1]
        print()
        if isinstance(output, tuple):
            output[0](output[1])
        else:
            output()
    
    def abort(self):
        print("Aborting")
        sys.exit()

    def print_stats_and_times(self, inbox):
        print(inbox.get_stats())
        print(inbox.get_times())

class Analyze:
    def __init__(self, diags):
        self.diags = diags

    def get_graph(self, inbox):
        self.diags.select_users(inbox)
        

def main():
    parser = argparse.ArgumentParser(description='Analyze data downloaded from facebook')
    parser.add_argument('-i', dest='path_in', required=True, default='', help='Path to the inbox folder')
    parser.add_argument('-o', dest='path_out', required=False, default='', help='Path to the output folder')

    args = parser.parse_args()

    args.path_in = os.path.normpath(args.path_in)
    if args.path_out == "":
        args.path_out = args.path_in[0:args.path_in.index("/messages") + 1]
        print("Path out set to:", args.path_out)
    
    
    print("Loading files...")
    inbox = fb.Inbox(args.path_in)

    diags = Dialogs()
    analyze = Analyze(diags)

    print()
    diags.print_stats_and_times(inbox)

    menu = [
        ("Analyze", (analyze.get_graph, inbox)), 
        ("Select users", (diags.select_users, inbox)), 
        ("Print statistics", (diags.print_stats_and_times, inbox)), 
        ("Abort", diags.abort)
    ]
    while True:
        diags.print_numbered_menu_methods(menu)
        


if __name__ == '__main__':
    main()