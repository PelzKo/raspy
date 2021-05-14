#!/usr/bin/env python3

import argparse
import gettext
import json
import os
import queue
import sys
from datetime import datetime

import pyttsx3
import sounddevice as sd
import vosk

import modules

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


q = queue.Queue()


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-m', '--model_base', type=str, metavar='MODEL_PATH',
    help='Path to the base dir of all models')
parser.add_argument(
    '-g', '--logs', type=str, metavar='LOGS_PATH',
    help='Path to the logs')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, help='sampling rate')
args = parser.parse_args(remaining)

try:
    if args.model_base is None:
        args.model_base = "models"
    args.model_base += "/model_" + config.language
    if not os.path.exists(args.model_base):
        print("Error finding the model at "+args.model_base+". Please refer to https://alphacephei.com/vosk/models")
        parser.exit(0)
    if args.logs is None:
        args.logs = "../logs"
    if not os.path.exists(args.logs):
        print("Please supply the correct path to the logs folder.")
        parser.exit(0)
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info['default_samplerate'])

    base_dir = args.logs.split("/logs")[0]

    # The translations were implemented in accordance with https://phrase.com/blog/posts/translate-python-gnu-gettext/
    language = gettext.translation('base', localedir=base_dir+'/locales', languages=[config.language])
    language.install()
    _ = language.gettext  # The saved language in the config file

    model = vosk.Model(args.model_base)

    with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device, dtype='int16',
                           channels=1, callback=callback):

        log_file = args.logs + "/commands.log"

        rec = vosk.KaldiRecognizer(model, args.samplerate)
        listening = False
        no_command = False
        spoken_temp = ""
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.5)
        voices = engine.getProperty('voices')
        for voice in voices:
            if "_"+config.language in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break
        engine.say(_("Everything is set up, I am listening"))
        engine.runAndWait()
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                if result is None:
                    continue
                spoken = json.loads(result)['text'].lower()
                print(spoken)
                if _("hey raspy") in spoken or _("hey jeremiah") in spoken:
                    spoken_temp = spoken + " "
                    listening = True
                    engine.say(_("Yes?"))
                    engine.runAndWait()
                    continue

                if listening:
                    spoken = spoken_temp + spoken
                    if _("note") in spoken:
                        modules.write_note_to_telegram(spoken, engine)
                    elif _("weather") in spoken:
                        modules.get_weather(spoken, engine)
                    elif _("random number") in spoken:
                        pass
                    elif _("coin") in spoken:
                        pass
                    elif _("reboot") in spoken:
                        os.system("/usr/bin/sudo /sbin/shutdown -r now")
                    elif _("shutdown") in spoken:
                        os.system("/usr/bin/sudo /sbin/shutdown")
                    elif _("switch language") in spoken or _("switch the language") in spoken:
                        next_language = spoken.split(_("to"))[1].split(" ")[1]
                        next_language_short = "invalid"
                        if next_language == _("german"):
                            next_language_short = "de"
                        elif next_language == _("english"):
                            next_language_short = "en"
                        else:
                            engine.say(_("Language")+" "+next_language+" "+ _("not recognized"))
                            engine.runAndWait()

                        if next_language_short != "invalid":
                            with open('../config.py', 'r+') as f:
                                file_source = f.read()
                                f.seek(0)
                                f.write("language=\""+next_language_short+"\"\n"+file_source.split("\n",maxsplit=1)[1])
                                f.truncate()
                            os.system("/usr/bin/sudo /sbin/shutdown -r now")
                    else:
                        no_command = True
                    if not no_command:
                        with open(log_file, "a") as log:
                            log.write(f"{datetime.now()}\t{spoken}")
                    no_command = False
                    listening = False
                    spoken_temp = ""

except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
