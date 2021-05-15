#!/usr/bin/env python3

import argparse
import gettext
import json
import os
import queue
import sys
import random
import requests
import threading

from word2number import w2n
from datetime import datetime

import pyttsx3
import sounddevice as sd
import vosk

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


# Built with https://sarafian.github.io/low-code/2020/03/24/create-private-telegram-chatbot.html
def write_note_to_telegram(spoken, engine):
    note = spoken.split(_("note"))[1]
    url = f'https://api.telegram.org/bot1726688721:AAHvsorK7sEMhkf0mFsT2XmSaIWbhAYOiE8/sendMessage?chat_id=-586897211&text={note}'
    r = requests.get(url=url)
    # extracting data in json format
    data = r.json()
    if data['ok'] is not True:
        print("An error has occurred")
        print(data['result'])
        engine.say(_("Encountered an error writing the note"))
    else:
        engine.say(f'{_("Wrote down the note: ")} {note}')

    engine.runAndWait()


def get_weather(spoken, engine):
    everything = spoken.split(_("weather"))[1]
    split = everything.split(" ")
    date_term = split[2]
    time_term = split[4]

    #if place_term.lower() != "innsbruck":
    #    say_with_engine(engine, _("Currently, only Innsbruck is supported"))
    #    return None


 #   time_possibilities = ["today", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday",
 #                         "saturday", "sunday"]
 #   for possibility in time_possibilities:
 #       if possibility in spoken:
 #           if possibility is "on the":
 #               pass
 #               break
 #           time_term = possibility
 #           break





    with open('weather.json', 'r') as json_file:
        data = json.load(json_file)

    current_time = datetime.now()
    do_request = True
    if "timestamp" in data:
        last_time_requested = data["timestamp"]
        date_time_obj = datetime.strptime(last_time_requested, '%Y-%m-%d %H:%M:%S.%f')
        difference = current_time - date_time_obj
        do_request = difference.total_seconds()*60 > 60
    if do_request:
        # Hardcoded: Todo Change to acomodate all cities
        lat = "47.260162"
        lon = "11.349379"
        part = "current,alerts"
        api_key = "f6e1716a5a1d1881b048e5fa4b6acde0"
        unit = "metric"
        url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={part}&appid={api_key}&units={unit}'
        r = requests.get(url=url)
        # extracting data in json format
        data = r.json()
        data["timestamp"] = current_time
        with open('weather.json', 'w') as json_file:
            json.dump(data, json_file)

    if r.__getattribute__("status_code") != 200:
        print("An error has occurred")
        print(data)
        engine.say(_("Encountered an error getting the weather"))
    else:
        engine.say(f'{_("Wrote down the note: ")} {unit}')

    engine.runAndWait()


def say_random_number(spoken, engine):
    needed = spoken.split(_("between"))[1]
    number_split = needed.split(_("and"))
    one = w2n.word_to_num(number_split[0])
    two = w2n.word_to_num(number_split[1])

    from_num = min(one, two)
    to_num = max(one, two)

    engine.say(f'{_("The number between")} {from_num} {_("and")} {to_num} {_("is")} {random.randint(from_num, to_num)}')
    engine.runAndWait()
    return None


def set_timer(spoken, engine):
    everything = spoken.split(_("for"))[1]
    seconds_amount = 0
    if _("second") in everything:
        seconds_amount += w2n.word_to_num(everything.split("second")[0])
    elif _("minute") in everything:
        seconds_amount += 60*w2n.word_to_num(everything.split("minute")[0])
    elif _("hour") in everything:
        seconds_amount += 60*60*w2n.word_to_num(everything.split("hour")[0])
    else:
        say_with_engine(engine, f'{_("Sorry, but I did not understand for")} {everything}')
        return None

    to_say = ""
    if _("note") in everything:
        to_say = everything.split(_("note"))[1]
    elif _("text") in everything:
        to_say = everything.split(_("text"))[1]

    start_time = threading.Timer(seconds_amount, say_with_engine, [engine, f'{_("Timer is up")} {to_say}'])
    start_time.start()


def say_with_engine(engine, text):
    engine.say(text)
    engine.runAndWait()


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
    args.model_base = f'{args.model_base}/model_{config.language}'
    if not os.path.exists(args.model_base):
        print(f'Error finding the model at {args.model_base}. Please refer to https://alphacephei.com/vosk/models')
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
    language = gettext.translation('base', localedir=f'{base_dir}/locales', languages=[config.language])
    language.install()
    _ = language.gettext  # The saved language in the config file

    model = vosk.Model(args.model_base)

    with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device, dtype='int16',
                           channels=1, callback=callback):

        log_file = f'{args.logs}/commands.log'

        rec = vosk.KaldiRecognizer(model, args.samplerate)
        listening = False
        no_command = False
        spoken_temp = ""
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.5)
        voices = engine.getProperty('voices')
        for voice in voices:
            if f'_{config.language}' in voice.id.lower():
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
                    spoken_temp = spoken
                    listening = True
                    engine.say(_("yes?"))
                    engine.runAndWait()
                    continue

                if listening:
                    spoken = f'{spoken_temp} {spoken}'
                    if _("note") in spoken:
                        write_note_to_telegram(spoken, engine)
                    elif _("weather") in spoken:
                        get_weather(spoken, engine)
                    elif _("random number") in spoken:
                        say_random_number(spoken, engine)
                    elif _("timer") in spoken:
                        set_timer(spoken, engine)
                    elif _("coin") in spoken:
                        if random.choice([True, False]):
                            engine.say(_("Head"))
                        else:
                            engine.say(_("Tails"))
                        engine.runAndWait()
                    elif _("reboot") in spoken:
                        engine.say(_("Rebooting"))
                        engine.runAndWait()
                        os.system("/usr/bin/sudo /sbin/shutdown -r now")
                    elif _("shutdown") in spoken:
                        engine.say(_("Shutting down"))
                        engine.runAndWait()
                        os.system("/usr/bin/sudo /sbin/shutdown now")
                    elif _("language") in spoken and (_("switch") in spoken or _("change") in spoken):
                        next_language = spoken.split(_("to"))[1].split(" ")[1]
                        next_language_short = "invalid"
                        if next_language == _("german"):
                            next_language_short = "de"
                        elif next_language == _("english"):
                            next_language_short = "en"
                        else:
                            engine.say(f'{_("language")} {next_language} {_("not recognized")}')
                            engine.runAndWait()

                        if next_language_short != "invalid":
                            with open('../config.py', 'r+') as f:
                                file_source = f.read()
                                f.seek(0)
                                rest_of_text = file_source.split("\n", maxsplit=1)[1]
                                f.write(f'language=\"{next_language_short}\"\n{rest_of_text}')
                                f.truncate()
                            os.system("/usr/bin/sudo /sbin/shutdown -r now")
                    else:
                        no_command = True
                    if not no_command:
                        with open(log_file, "a") as log:
                            log.write(f'{datetime.now()}\t{spoken}\n')
                    no_command = False
                    listening = False
                    spoken_temp = ""

except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
