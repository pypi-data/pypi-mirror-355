from . import http_client, api
import json, re

login = json.load(open('login.json', 'r'))

class NotFound(Exception):
    ...

def get_id_info(id: str) -> dict:
    """ get user id info, example
        .get_id_info('1')
        -> {"id":"1","username":"Gargron","acct":"Gargron","display_name":"Eugen Rochko",..... }
    """
    url_id = f'{api}/v1/accounts/{id}'
    response = http_client.rq_get(url= url_id, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    })
    if 'error' in response.text:
        raise NotFound(
            f"User {id} not found!"
        )
    return (json.loads(response.text))

def get_username_info(username: str) -> dict:
    """ get username information """
    url = f'{api}/v1/accounts/lookup?acct={username}'
    response = http_client.rq_get(
        url= url, headers= login
    )
    if 'error' in response.text:
        raise NotFound(
            f"{username} not found!"
        )
    return (get_id_info(json.loads(response.text)['id']))

def get_following(id: str, limit: str) -> dict:
    """ get following by limit
    .get_following('1', limit= 10)
    """
    url = f'{api}/v1/accounts/{id}/following?limit={limit}'
    response = http_client.rq_get(
        url= url, headers= login
    )
    return json.loads(response.text)

def get_followers(id: str, limit: str) -> dict:
    """ get followers by limit
    .get_followers('1', limit= 10)
    """
    url = f'{api}/v1/accounts/{id}/followers?limit={limit}'
    response = http_client.rq_get(
        url= url, headers= login
    )
    return json.loads(response.text)

def follow(id: str) -> list:
    url = f'{api}/v1/accounts/{id}/follow'
    response = http_client.rq_post(
        url= url, headers= login, data={'reblogs': True}
    )
    return json.loads(response.text)

def unfollow(id: str) -> list:
    url = f'{api}/v1/accounts/{id}/follow'
    response = http_client.rq_post(
        url= url, headers= login
    )
    return json.loads(response.text)