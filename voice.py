#!/usr/bin/env python3

import argparse
import ast
import os
import queue
import sounddevice as sd
import vosk
import sys
import openai
import subprocess


q = queue.Queue()

word_dict = {}


def ask_chatGTP_question(question):

    openai.api_key = "sk-dfsdfsdfsaopfisfasfasdfblank"
    model_engine   = "text-ada-001"
    prompt         = question

    completion     = openai.Completion.create(
        engine     = model_engine,
        prompt     = prompt,
        max_tokens = 1024,
        n          = 1,
        stop       = None,
        temperature= 0.5,
    )

    response = completion.choices[0].text
    return response


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
#    if status:
#        print(status, file=sys.stderr)
    q.put(bytes(indata))


model_path = '/home/deatheater/Downloads/vosk-model-en-us-0.22-lgraph'
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-l', '--list-devices', action='store_true', help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter, parents=[parser])
parser.add_argument('-f', '--filename', type=str, metavar='FILENAME',help='audio file to store recording to')
parser.add_argument('-d', '--device', type=int_or_str,help='input device (numeric ID or substring)')
parser.add_argument('-r', '--samplerate', type=int, help='sampling rate')
args = parser.parse_args(remaining)


def check_for_close(words):
    for word in words.split(' '):
        if word == 'shutdown' or word == 'close' or word == 'exit':
            exit('')


class Voice():

    stuCount = 0


    def listen(self):

        try:
            if args.samplerate is None:
            
                device_info = sd.query_devices(args.device, 'input')
                args.samplerate = int(device_info['default_samplerate'])

            model = vosk.Model(lang="en-us")

            if args.filename:
                dump_fn = open(args.filename, "wb")
            else:
                dump_fn = None

            with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device, dtype='int16',
                                   channels=1, callback=callback) as voice:

                open_something = False
                find_something = False
                listening      = False
                listened       = False
                task_run       = False
                note_something = False
                heard          = ''
                note_taken     = False
                rec            = vosk.KaldiRecognizer(model, args.samplerate)
                dictated       = []
                journal        = False
                ask_chatGTP    = False
                asked_chatGTP  = False
                
                while True:
                
                    data = q.get()
                    
                    if rec.AcceptWaveform(data):

                        text = ast.literal_eval(rec.Result())
                        print('text {}'.format(text))


                        if text['text'] != '':
                            words = text['text']

                            check_for_close(words)
                                
                            if words.split(' ')[0] == 'open':
                                open_something = True
                            
                            if words == 'take note' or words == 'take notes':
                                note_something = True
                                note_taken     = False
                                
                            if words == 'ask internet':
                                ask_chatGTP   = True
                                asked_chatGTP = False
                                
                            
                        if ask_chatGTP and listening:

                            os.system('clear')
                            print('Ask away...')
                            
                            if words == 'type it in' or words == 'manual':
                                dictated = input('Please type in your question ?')
                                dictated = [dictated]
                                words = 'send it'
                            
                            if words == 'show me' or words == 'list':
                                os.system('jrnl {} -n 50'.format(journal))
                            elif words == 'clear':
                                dictated = []
                            elif words == 'remove' or words == 'delete' or 'take note' in dictated or 'take notes' in dictated:
                                if dictated:
                                    dictated.pop()
                            elif words in ['send it', "that's it"]:
                                
                                question = ' '.join(dictated)
                                answer   = ask_chatGTP_question(question)
                                print(answer)
                                input('continue press any key...')
                                ask_chatGTP    = False
                                listening      = False
                                dictated       = []
                                words          = ''
                                
                            elif words not in dictated:
                                dictated.append(words)
                                n = 1
                                for dictation in dictated:
                                    print('jrnl {} {} {}'.format(journal, n, dictation))
                                    n += 1

                            elif words in ['go away']:

                                note_taken = True
                                listening  = False
                                dictated   = []
                                words      = ''
                                    
                        elif not note_taken and listening:

                            os.system('clear')
                            print('starting to think')
                            
                            if 'work' == words and not dictated:
                                journal = 'work'
                                dictated = []
                                words    = ''

                            
                            if 'private' == words and not dictated:
                                journal = 'private'
                                dictated = []
                                words    = ''
                            
                            if journal == 'private' or journal == 'work' and words:
                            
                                if words == 'show me' or words == 'list':
                                    os.system('jrnl {} -n 50'.format(journal))
                                elif words == 'clear':
                                    dictated = []
                                elif words == 'remove' or words == 'delete' or 'take note' in dictated or 'take notes' in dictated:
                                    if dictated:
                                        dictated.pop()
                                elif words in ['send', "that's it"]:

                                    n = 1
                                    for dictation in dictated:
                                    
                                        os.system("jrnl {} {} {}".format(journal, n, dictation.replace("'", "").replace('"', "")))
                                        
                                        n += 1

                                        note_something = False
                                        note_taken     = False
                                        dictated       = []
                                        words          = ''

                                elif words not in dictated:
                                    dictated.append(words)
                                    n = 1
                                    for dictation in dictated:
                                        print('jrnl {} {} {}'.format(journal, n, dictation))
                                        n += 1

                                elif words in ['go away']:

                                    note_taken = True
                                    listening  = False
                                    dictated   = []
                                    words      = ''
                            else:
                                if not journal:
                                    print('journal name?')

                        else:

                            if listening:
                                os.system('clear')
                                print("Yes, I', listening")
                                listening = True

                            if note_something:
                                os.system('clear')
                                print("Taking notes")
                                listening = True
                                
                            if ask_chatGTP:
                                os.system('clear')
                                print("ask_chatGTP test")
                                listening = True

        except KeyboardInterrupt:
            print('\nDone')
            parser.exit(0)
        except Exception as e:
            parser.exit(type(e).__name__ + ': ' + str(e))

stu1 = Voice()
stu1.listen()

