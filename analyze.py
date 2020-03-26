import argparse, os
import fb_disassemble as fb

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
    user = fb.Inbox(args.path_in)
    
    user.select_based_on_percentage(80)

    print()
    for chat in user.get_selected():
        print(chat.get_debug())
    
    print(user.get_stats())
    print(user.get_times())



if __name__ == '__main__':
    main()