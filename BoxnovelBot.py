import json, requests, os
from flask import Flask, request

from readers import (Reader,
    NoUserData, NoFavoritedNovel, AlreadyFavorited, UserAlreadyExist, FavoriteNovelDoesNotExist,
    InvalidNovelTitle,
    )

PAGE_TOKEN = os.environ['PAGE_TOKEN']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
jsonpath = './users.json'
reader = Reader(jsonpath)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World'

@app.route('/health')
def health():
    print('alive')
    return 'alive'

@app.route('/webhook', methods=['GET'])
def webhookget():
    print('get')
    if (request.args.get('hub.verify_token', '') == VERIFY_TOKEN):
        print("Verified")
        return request.args.get('hub.challenge', '')
    else:
        print('not verified')
        return "Error, wrong validation token"

@app.route('/webhook', methods=['POST'])
def webhookpost():
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    message_text = messaging_event["message"]["text"]
                    # ---------------------- HANDLE RECEIVED TEXT ------------------------
                    print('received')
                    print(sender_id)
                    if message_text.lower() == 'user()':
                        try:
                            response = reader.user(sender_id)
                            send_message(sender_id, response)
                        except NoUserData:
                            send_message(sender_id, 'No User Data,\nTry typing <newUser()>.')
                    elif message_text.lower() == 'favorites()':
                        try:
                            response = reader.favorites(sender_id)
                            send_message(sender_id, response)
                        except NoUserData:
                            send_message(sender_id, 'No User Data')
                        except NoFavoritedNovel:
                            send_message(sender_id, 'You Did not Favorite a Novel Yet')
                    elif 'newuser(' in message_text.lower():
                        try:
                            args = getargs(message_text)
                            if len(args) == 1:
                                response = reader.newUser(sender_id, username=args[0])
                            else:
                                response = reader.newUser(sender_id)
                            send_message(sender_id, response)
                        except UserAlreadyExist:
                            send_message(sender_id, 'User Data Already Logged')
                    elif 'newfavorite' in message_text.lower():
                        try:
                            args = getargs(message_text)
                            if len(args) == 1:
                                response = reader.newFavorite(sender_id, args[0])
                            elif len(args) == 2:
                                response = reader.newFavorite(sender_id, args[0], int(args[1]))
                            else:
                                response = 'Novel not added'
                            send_message(sender_id, response)
                        except NoUserData:
                            send_message(sender_id, 'No User Data')
                        except AlreadyFavorited:
                            send_message(sender_id, 'Novel Already Favorited')
                    elif message_text.lower() == 'update()':
                        try:
                            response = reader.update(sender_id)
                            send_message(sender_id, response)
                        except NoUserData:
                            send_message(sender_id, 'No User Data')
                        except InvalidNovelTitle as e:
                            send_message(sender_id, f'Invalid Title @ {str(e)}')
                    elif 'removefavorite(' in message_text.lower():
                        try:
                            args = getargs(message_text)
                            response = reader.removeFavorite(sender_id, args[0])
                            send_message(sender_id, response)
                        except NoUserData:
                            send_message(sender_id, 'No User Data')
                        except FavoriteNovelDoesNotExist as e:
                            send_message(sender_id, f'Novel Does NOT EXIST in your list of favorited novels\nYou typed {str(e)}')
                    elif 'read(' in message_text.lower():
                        try:
                            args = getargs(message_text)
                            if len(args) == 2:
                                sentences = reader.read(sender_id, args[0], args[1])
                            else:
                                sentences = reader.read(sender_id, args[0])
                            response = ''
                            for sentence in sentences:
                                words = sentence.split(' ')
                                for word in words:
                                    if len(response) + len(word) > 1990:
                                        send_message(sender_id, response)
                                        response = ''
                                    response += f' {word}'
                                response += '\n'
                        except NoUserData:
                            send_message(sender_id, 'No User Data')
                        except InvalidNovelTitle:
                            send_message(sender_id, 'Invalid Novel Title')
                        except FavoriteNovelDoesNotExist:
                            send_message(sender_id, 'Novel does not exist in your favorites\nAdd the title to your favorites first')
                    elif message_text.lower() in ['help', '?']:
                        helptext = 'Command => Details\n'
                        helptext += 'user() => Display User Data\n\n'
                        helptext += 'newUser((opt)(str)<username>) => Create New User Data with optional username\n\n'
                        helptext += 'favorites() => Display User\'s Favorites with data\n\n'
                        helptext += 'newFavorite((str)<title>, (opt)(int)<lastreadchapter>) => Add Favorite Novel with optional data\n\n'
                        helptext += 'removeFavorite((str)<title>) => Remove novel from your favorites by the title given\n\n'
                        helptext += 'read((str)<title>, (opt)[<"next"> or (int)<chapter>] => Read from a title (in your favorites) optional options: next-> read next chapter; chapter->read at certain chapter; if empty read the last read chapter))\n\n'
                        send_message(sender_id, helptext)
                    else:
                        text = 'Type "help" or "?" to get help text'
                        send_message(sender_id, text)

    return "ok"

def send_message(sender_id, message_text):
    '''
    Sending response back to the user using facebook graph API
    '''
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",

        params={"access_token": PAGE_TOKEN},

        headers={"Content-Type": "application/json"},

        data=json.dumps({
        "recipient": {"id": sender_id},
        "message": {"text": message_text}
    }))

def getargs(msg):
    return msg[msg.find('(')+1:msg.find(')')].split(',')
# def bsthis(bsdata, *args, **kwargs):
#     if args:
#         pass
#     if kwargs:
#         for key, value in kwargs.items():
#             if key == 'class_':
#                 return bsdata.find(class_=value)

# url = 'https://boxnovel.com/novel/i-alone-level-up/chapter-'

# jeju_urls = []

# for i in range(100,101):
#     nurl = f'{url}{i}'
#     response = requests.get(nurl)
#     page = bs(response.text, 'html.parser')
#     cont = bsthis(page, class_='entry-content')
#     readcont = bsthis(cont, class_='reading-content')
#     text = bsthis(readcont, class_='text-left')
#     print(text.text)

if __name__ == "__main__":
    app.run()