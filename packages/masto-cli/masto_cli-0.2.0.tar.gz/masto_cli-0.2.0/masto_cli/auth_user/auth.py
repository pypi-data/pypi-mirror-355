from masto_cli import http_client
import re

class CookieError(Exception):
    ...

class Authdata:
    """ i don't know why but just do it....."""
    def __init__(self) -> None:
        self.url = 'https://mastodon.social/home'

    def get_authorization(self, html: str) -> str:
        """ need for headers
            "authorization": "Bearer OlyGa6FDGy......" 
         """
        return re.search(r'{"meta":{"access_token":"(.*?)",', html)[1]

    def get_xcsrftoken(self, html: str) -> str:
        """ need for headers
            "x-csrf-token": "0e68vqPLCn..."
        """
        return re.search(r'name="csrf-token" content="(.*?)"', html)[1]

    def get(self, cookie: str) -> dict[str, str]:
        headers = {
            "cookie": cookie,
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }
        response = http_client.rq_get(
            self.url, headers=headers
        )
        try:
            authorization = self.get_authorization(response.text)
            xcsrftoken = self.get_xcsrftoken(response.text)
            return {
                "cookie": cookie,
                "authorization": f"Bearer {authorization}",
                "x-csrf-token": xcsrftoken
            }
        except:
            raise CookieError("Cookie error")
