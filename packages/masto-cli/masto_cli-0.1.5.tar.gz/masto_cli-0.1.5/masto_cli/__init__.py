from .sign_in.sign_in import Login
from .sign_in import http_client
from .sign_in import html_parser
from .auth_user import Authdata
from .profile import (
    get_id_info, get_username_info, get_following,
    get_followers, login, follow, unfollow
)
from .timeline import get_timeline, get_post_info
from .publish import Publish
from .favourite import favourite

api = 'https://mastodon.social/api'

login = Login()
auth = Authdata()