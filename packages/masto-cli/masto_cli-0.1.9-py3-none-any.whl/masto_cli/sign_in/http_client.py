import requests

session = requests.Session()

def rq_get(url, headers= None):
    return (
        session.get(url= url, headers= headers)
    )

def rq_post(url, data=None, json=None, headers=None, files=None):
    return (
        session.post(url= url, data=data, json=json, headers= headers, files=files))