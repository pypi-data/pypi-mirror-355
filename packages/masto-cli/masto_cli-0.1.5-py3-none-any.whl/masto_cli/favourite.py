from . import login
from . import http_client, api
import json

def favourite(post_id: str) -> list:
    url = f'{api}/v1/statuses/{post_id}/favourite'
    response = http_client.rq_post(
        url= url, headers= login
    )
    return (json.loads(response.text))