import requests


#Built with https://sarafian.github.io/low-code/2020/03/24/create-private-telegram-chatbot.html
def write_note_to_telegram(spoken):
    note = spoken.split("note")[1]
    URL = "https://api.telegram.org/bot1726688721:AAHvsorK7sEMhkf0mFsT2XmSaIWbhAYOiE8/sendMessage" \
          "?chat_id=-586897211&text=" + note
    r = requests.get(url=URL)
    # extracting data in json format
    data = r.json()
    if data['ok'] is not True:
        print("An error has occurred")
        print(data['result'])


def get_weather(spoken):
    place_term = None
    place_possibilities = ["city", "country", "weather in", "weather like in"]
    for possibility in place_possibilities:
        if possibility in spoken:
            place_term = possibility
            break

    time_term = None
    time_possibilities = ["today", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday",
                          "saturday", "sunday", "on the"]
    for possibility in place_possibilities:
        if possibility in spoken:
            if possibility is "on the":
                pass
                break
            time_term = possibility
            break
