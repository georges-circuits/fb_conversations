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
    def __init__(self, )

class User:
    def __init__(self, name, meta, messages):
        self.name = name
        self.meta = meta
        self.messages = messages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze data downloaded from facebook')
    parser.add_argument('-i', dest='path_in', required=True, default='', help='Path to the inbox folder')
    parser.add_argument('-o', dest='path_out', required=False, default='', help='Path to the output folder')

    args = parser.parse_args()


