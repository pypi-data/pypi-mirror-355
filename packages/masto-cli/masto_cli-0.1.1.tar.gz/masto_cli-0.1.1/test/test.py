from mastobot import (
    login, auth, get_id_info, get_username_info,
    get_following, get_followers, get_timeline,
    Publish
)
import json
# import colorama
# from colorama import Fore, Style, Back
# colorama.init()


def signIn(email, password):
    try:
        signIn = auth.get(
            login.get_cookie(email= email, password= password))
        json.dump(signIn, open("login.json", "w"))
        return signIn
    except Exception as e:
        print(f"Error: {e}")

with open('login.json', 'r') as user:
    user = json.load(user)
    if 'cookie' in user:
        try:
            # i = 1
            # info = get_following(get_username_info('realsifocopypaste')['id'], limit=10)
            # for data in info:
            #     print(f"[ {i} ] {Fore.BLUE}ID{Fore.RESET}: {data['id']} {Fore.BLUE}USERNAME{Fore.RESET}: {data['username']} {Fore.BLUE}NAME{Fore.RESET}: {data['display_name']}")
            #     i+=1
            # timeline = get_timeline()
            # for data in timeline:
            #     print(data)
            ...
        except Exception as e:
            print(e)
    else:
        user = signIn("youremail@gmail.com", "password")

media_path = ["assets/wpp.jpg", "assets/wpp2.jpg"]

# Publish(text="Send status from python", media_path= media_path).status()