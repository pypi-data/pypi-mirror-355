from masto_cli.sign_in.sign_in import Login
from masto_cli.sign_in import http_client
from masto_cli.sign_in import html_parser
from masto_cli.auth_user import Authdata
from masto_cli.profile import (
    get_id_info, get_username_info, get_following,
    get_followers, login, follow, unfollow
)
from masto_cli.timeline import get_timeline, get_post_info
from masto_cli.publish import Publish
from masto_cli.favourite import favourite

api = 'https://mastodon.social/api'

login = Login()
auth = Authdata()