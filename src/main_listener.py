#!/usr/bin/env python3

import argparse
import gettext
import json
import os
import queue
import sys
import random
from os.path import exists

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
def write_note_to_telegram(spoken):
    note = spoken.split(_("note"))[1]
    url = f'https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage?chat_id=-586897211&text={note}'
    r = requests.get(url=url)
    # extracting data in json format
    data = r.json()
    if data['ok'] is not True:
        print("An error has occurred")
        print(data['result'])
        say_with_engine(_("Encountered an error writing the note"))
    else:
        say_with_engine(f'{_("Wrote down the note: ")} {note}')


def difference_next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return days_ahead


def difference_next_hour_or_weekday(d, weekday, hour):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    hours_ahead = hour - d.hour
    hours_ahead += days_ahead * 24
    if hours_ahead <= 48:
        return hours_ahead, True
    return days_ahead, False


# Currently, only Innsbruck is supported
def get_weather(spoken):
    everything = spoken.split(_("weather"))[1]
    split = everything.split(" ")
    if _("for") in split:
        split.remove(_("for"))
    if _("at") in split:
        split.remove(_("at"))
    if len(split) < 2:
        say_with_engine(_("Please state a date or a date and time"))
        return None
    date_term = split[1]
    time_term = None
    if len(split) > 2:
        time_term = w2n.word_to_num(split[2])
        if len(split) > 3:
            if split[3] == "pm":
                time_term += 12

    relative_terms = ["today", "tomorrow"]
    absolute_terms = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    if date_term in relative_terms:
        date_number = relative_terms.index(date_term)
    elif date_term in absolute_terms:
        date_number = absolute_terms.index(date_term)
    else:
        say_with_engine(f'{_("String")} {date_term} {_("is not valid")}')
        return None

    data = {}

    if exists("weather.json"):
        with open('weather.json', 'r') as json_file:
            data = json.load(json_file)

    current_time = datetime.now()
    do_request = True
    if "timestamp" in data:
        last_time_requested = data["timestamp"]
        date_time_obj = datetime.strptime(last_time_requested, '%Y-%m-%d %H:%M:%S.%f')
        difference = current_time - date_time_obj
        do_request = difference.total_seconds() / 60 > 60
    if do_request:
        # Hardcoded: Todo Change to acomodate all cities
        lat = "47.260162"
        lon = "11.349379"
        part = "current,alerts,minutely"
        api_key = config.weather_api_token
        unit = "metric"
        language = config.language
        url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={part}&appid={api_key}&units={unit}&lang={language}'
        r = requests.get(url=url)
        if r.__getattribute__("status_code") != 200:
            print("An error has occurred")
            print(r)
            with open(log_file, "a") as log:
                log.write(f'ERR\t{datetime.now()}\t{r}\n')
            say_with_engine((_("Encountered an error getting the weather")))
            return None
        # extracting data in json format
        data = r.json()
        data["timestamp"] = str(current_time)
        with open('weather.json', 'w') as json_file:
            json.dump(data, json_file)

    if time_term >= 0:
        if date_term in relative_terms:
            date_number = (current_time.weekday() + date_number) % 7
        time_difference = difference_next_hour_or_weekday(current_time, date_number, time_term)
        if time_difference[1]:
            weather = data["hourly"][time_difference[0]]["weather"][0]["description"]
            temp = data["hourly"][time_difference[0]]["temp"]
            prob_rain = data["hourly"][time_difference[0]]["pop"] * 100

            to_say = f'{date_term} {_("at")} {time_term} {_("o clock the weather will be")} {weather}. {_("It will be")} {temp} {_("degrees celsius and the probability for rain is")} {prob_rain} {_("percent")}'
            say_with_engine(to_say)

            return None
        else:
            day_difference = time_difference[0]
    else:
        if date_term in relative_terms:
            day_difference = date_number
        else:
            day_difference = difference_next_weekday(current_time, date_number)

    if day_difference == -1:
        with open(log_file, "a") as log:
            log.write(f'ERR\t{datetime.now()}\t{date_term}\t{time_term}\n')
        say_with_engine((_("Encountered an error getting the weather")))
        return None

    weather = data["daily"][day_difference]["weather"][0]["description"]
    temp_day = data["daily"][day_difference]["temp"]["day"]
    temp_eve = data["daily"][day_difference]["temp"]["eve"]
    prob_rain = data["daily"][day_difference]["pop"] * 100

    to_say = f'{date_term} {_("the weather will be")} {weather}. {_("It will be")} {temp_day} {_("degrees celsius during the day and")} {temp_eve} {_("degrees celcius during the evening. The probability for rain is")} {prob_rain} {_("percent")}'
    say_with_engine(to_say)


def say_random_number(spoken):
    needed = spoken.split(_("between"))[1]
    number_split = needed.split(_("and"))
    one = w2n.word_to_num(number_split[0])
    two = w2n.word_to_num(number_split[1])

    from_num = min(one, two)
    to_num = max(one, two)

    say_with_engine(
        f'{_("The number between")} {from_num} {_("and")} {to_num} {_("is")} {random.randint(from_num, to_num)}')
    return None


def set_timer(spoken):
    everything = spoken.split(_("for"))[1]
    seconds_amount = 0
    if _("second") in everything:
        seconds_amount += w2n.word_to_num(everything.split("second")[0])
    elif _("minute") in everything:
        seconds_amount += 60 * w2n.word_to_num(everything.split("minute")[0])
    elif _("hour") in everything:
        seconds_amount += 60 * 60 * w2n.word_to_num(everything.split("hour")[0])
    else:
        say_with_engine(f'{_("Sorry, but I did not understand for")} {everything}')
        return None

    to_say = ""
    if _("note") in everything:
        to_say = everything.split(_("note"))[1]
    elif _("text") in everything:
        to_say = everything.split(_("text"))[1]

    start_time = threading.Timer(seconds_amount, say_with_engine, [f'{_("Timer is up")} {to_say}'])
    start_time.start()


def say_with_engine(text):
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
        voice_id_en = None
        voice_id_normal = None

        for voice in voices:
            if '_en' in voice.id.lower():
                voice_id_en = voice.id
                if voice_id_normal is not None:
                    break
            if f'_{config.language}' in voice.id.lower():
                voice_id_normal = voice.id
                if voice_id_en is not None:
                    break
        engine.setProperty('voice', voice_id_normal)
        say_with_engine(_("Everything is set up, I am listening"))
        while True:
            try:
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
                            write_note_to_telegram(spoken)
                        elif _("weather") in spoken:
                            get_weather(spoken)
                        elif _("random number") in spoken:
                            say_random_number(spoken)
                        elif _("timer") in spoken:
                            set_timer(spoken)
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
                        elif _("shut down") in spoken:
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
                                if exists("weather.json"):
                                    os.remove("weather.json")
                                os.system("/usr/bin/sudo /sbin/shutdown -r now")
                        else:
                            no_command = True
                            say_with_engine(f'{_("Could not understand")}: {spoken}')
                        if not no_command:
                            with open(log_file, "a") as log:
                                log.write(f'CMD\t{datetime.now()}\t{spoken}\n')
                        no_command = False
                        listening = False
                        spoken_temp = ""
            except Exception as ex:
                err_text = type(ex).__name__ + ': ' + str(ex)
                print(err_text)

                engine.setProperty('voice', voice_id_en)
                say_with_engine(err_text)
                engine.setProperty('voice', voice_id_normal)

                with open(log_file, "a") as log:
                    log.write(f'ERR\t{datetime.now()}\t{err_text}\n')

except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
