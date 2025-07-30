from masto_cli import http_client, login
from masto_cli.config import api
import json

def get_timeline() -> dict:
    """ get home time line """
    url = f"{api}/v1/timelines/home"
    response = http_client.rq_get(
        url= url, headers= login
    )
    return (json.loads(response.text))

def get_post_info(post_id: str) -> dict:
    """ get post information """
    url = f'{api}/v1/statuses/{post_id}/context'
    response = http_client.rq_get(
        url= url, headers= login
    )
    return (json.loads(response.text))