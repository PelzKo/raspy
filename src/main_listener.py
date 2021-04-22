#!/usr/bin/env python3

import argparse
import os
import queue
import sounddevice as sd
import vosk
import sys
import json
import pyttsx3
from datetime import datetime

import gettext
_ = gettext.gettext

import modules

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
    '-m', '--model', type=str, metavar='MODEL_PATH',
    help='Path to the model')
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
    if args.model is None:
        args.model = "model"
    if not os.path.exists(args.model):
        print("Please download a model for your language from https://alphacephei.com/vosk/models and unpack as "
                "'model' in the current folder.")
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

    model = vosk.Model(args.model)

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
        engine.setProperty('voice', voices[1].id)
        engine.say(_("Everything is set up, I am listening"))
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
                        pass
                    elif _("shutdown") in spoken:
                        pass
                    elif _("switch languge") in spoken or _("switch the languge") in spoken:
                        pass
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
