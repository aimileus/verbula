#!/usr/local/Cellar/verbula/1.1.1/libexec/bin/python3.6
"""
Python3 script to help you study your vocabulary

Copyright (C) 2018  Emiel Wiedijk

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import os
import readline
import random
import subprocess
import sys
import time
import unidecode


def say(text):
    return subprocess.Popen(['say', '-v', ARGS.voice, text])


def edit():
    # We split to handle spaces in EDITOR
    editor = os.getenv('EDITOR', 'nano').split()
    subprocess.run(editor + ARGS.lists)


class WordList:
    def __init__(self, list_files):
        self.start = time.time()
        self.list = []
        self.passes = 0
        self.fails = 0
        self.list_files = list_files

        # We obviously do not want history in this program
        readline.set_auto_history(False)

        for list_file in list_files:
            try:
                with open(list_file) as word_list_file:
                    for line in word_list_file:
                        if len(line.strip()) is 0:  # Do not add emtpy lines
                            pass
                        # Lines starting with a '#' are comments
                        elif line[0] == '#':
                            pass
                        else:
                            self.list.append(Item(line))
            except FileNotFoundError:
                print(f"Error: {list_file}, no such file or directory")
                sys.exit()
            except IsADirectoryError:
                print(f"Error: {list_file}, is a directory")
                sys.exit()
            random.shuffle(self.list)

        self.orig_len = len(self.list)

    def iterate(self):
        while self.list:
            word = self.list[0]
            user_answers = word.ask_answers()
            if word.check_answers(user_answers):
                self.answer_good()
            else:
                self.answer_false(word)
        self.finish()

    def answer_good(self):
        self.passes += 1
        self.list.pop(0)

    def answer_false(self, word):
        answers = " = ".join(word.answers)
        if word.type == 'dictation':
            print(word.question)
        else:
            print(f"{word.question} = {answers}")

        response = input()
        if 'e' in response:
            edit()
        if 'r' in response:
            self.restart()
            return
        if 'g' in response:
            self.answer_good()
            return

        self.list.pop(0)
        self.fails += 1
        self.list.append(word)
        self.list.insert(1, word)

    def restart(self):
        self.__init__(self.list_files)

    def finish(self, exitcode=0):
        subprocess.run(['clear'])
        print(f"{self.passes} answer(s) correct, \
{self.fails} answer(s) incorrect")
        end = time.time()
        elapsed = int(end - self.start)
        minutes = elapsed // 60
        seconds = elapsed % 60
        print(f'{minutes} minute(s) and {seconds} second(s) elapsed')
        sys.exit(exitcode)

    def print_status_bar(self):
        left_list = len(self.list)
        completion = left_list / self.orig_len
        try:
            columns = int(os.get_terminal_size().columns)
        except OSError:
            columns = 80
        if completion > 1:
            completion = 1
        counter = f'[{left_list}]'
        left_space = columns - len(counter)
        whitespace = ' ' * int(left_space * completion)
        bars = '#' * (columns - len(counter) - len(whitespace))
        print(f'{bars}{whitespace}{counter}')


def clear():
    subprocess.run(['clear'])
    WORD_LIST.print_status_bar()


def public_format(word):
    # Replace Apple's 'smart punctuation' with normal punctuation
    word = word.replace("’", "''")
    word = word.replace('”', '"')
    word = word.replace('…', '...')
    # Squash all whitespace into a single space
    word = ' '.join(word.split())
    # Remove whitespace at the end
    word = word.strip()
    return word


def private_format(word):
    # Ignore punctuation by removing these characters from the string
    if ARGS.strict:
        return ' '.join(word.split())
    punctuation_away = str.maketrans(',.+-;:\\/()!\'"?><!@#$%^&*±',
                                     '                         ')
    word = word.translate(punctuation_away)
    word = word.lower()  # Be case-insensitive.
    # Squash all whitespace into a single space
    word = ' '.join(word.split())
    word = word.strip()  # We split again in self.check_answer()
    if ARGS.unidecode:
        word = unidecode.unidecode(word)
    return word


def check_answer(answer, user_answer):
    """Return True if answer is correct, False if not."""
    user_answer = private_format(user_answer)
    answer = [private_format(item) for item in answer.split(',')]

    for item in answer:
        # The user must give all correct answers
        if item not in user_answer:
            return False
        user_answer = user_answer.replace(item, '', 1)

    return not user_answer.strip()


class Item:
    def __init__(self, words):
        """Load the question and answer(s) separated by an '='."""
        if ARGS.dictation:
            self.type = 'dictation'
            self.question = public_format(words)
            self.answers = [self.question]
            return

        words = [public_format(word) for word in words.split('=')]

        if ARGS.reverse:
            # The question is the last item in the list
            self.question = words.pop(-1)
        else:
            self.question = words.pop(0)
        self.answers = words

        if len(self.answers) == 1:
            self.type = 'singular'
        elif len(self.answers) > 1:
            self.type = 'plural'
        else:
            print(f'Error: "{self.question}", unexpected newline, \
expected "="')
            sys.exit(1)

    def ask_answers(self):
        """Return a list of what the user thinks the answer is."""
        clear()

        if self.type == 'singular':
            return self.ask_answers_singular()

        elif self.type == 'plural':
            return self.ask_answers_plural

        elif self.type == 'dictation':
            return self.ask_answers_dictation()

    def ask_answers_singular(self):
        answer = [input(f"{self.question} = ")]
        # Do not accept empty answers
        while answer == ['']:
            clear()
            answer = [input(f"{self.question} = ")]
        return answer

    def ask_answers_dictation(self):
        answer = ['']
        while answer == ['']:
            clear()
            say(self.question)
            answer = [input()]
        return answer

    @property
    def ask_answers_plural(self):
        len_question = len(self.question)
        before = (len_question * ' ') + " = "
        answers = [input(f"{self.question} = ")]

        for _ in range(len(self.answers)):
            answer = input(before)

            # The last answer must not be empty
            if answer == '':
                return self.ask_answers()
            answers.append(answer)

            return answers

    def check_answers(self, user_answers):
        """Return True if all answers in the list are correct, False if not."""
        for i, _ in enumerate(user_answers):
            if not check_answer(self.answers[i], user_answers[i]):
                return False
        return True


def quit_verbula(exitcode=0):
    print(ARGS)
    WORD_LIST.finish(exitcode)


def create_parser():
    parser = argparse.ArgumentParser('Get CLI options')
    parser.add_argument('lists', nargs='+',
                        help='the files that contain the lists')
    parser.add_argument('--reverse', '-r', action='store_true',
                        help='the question is the last item in the list')
    parser.add_argument('--unidecode', '-u', action='store_true',
                        help='represent unicode as ascii \
                        (i.e. remove accents)')
    parser.add_argument('--dictation', '-d', action='store_true',
                        help='use tts instead of print')
    parser.add_argument('--strict', '-s', action='store_true',
                        help="Don't ignore punctuation and capitals")
    parser.add_argument('--voice', help="Select which macOS tts voice verbula should use")
    return parser.parse_args()


if __name__ == '__main__':
    try:
        ARGS = create_parser()
        WORD_LIST = WordList(ARGS.lists)
        WORD_LIST.iterate()
    except KeyboardInterrupt:
        quit_verbula(exitcode=1)
    except EOFError:
        quit_verbula()
