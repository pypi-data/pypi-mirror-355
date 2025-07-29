from .http_client import rq_get, rq_post
from .html_parser import parse_html

class LoginError(Exception):
    ...

class Login:
    """ get cookies login """
    def __init__(self) -> None:
        self.login_url = 'https://mastodon.social/auth/sign_in'
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'referer': 'https://mastodon.social/auth/sign_in',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        }

    def authenticity_token(self) -> str:
        """ get authenticity token for login data 
            data = {
                'authenticity_token': self.authenticity_token(), <--- this
                'user[email]': email,
                'user[password]': password,
                'button': ''
            }
        """
        html_content = rq_get(
            url=self.login_url,
            headers=self.headers
        ).text
        token = parse_html(html_content).find("input", {"name": "authenticity_token"})["value"]
        return token
    
    def get_cookie(self, email: str, password: str) -> str:
        """ login and get cookie
            .get_cookie(email="youremail@gmail.com", password="password")
        """
        data = {
            'authenticity_token': self.authenticity_token(),
            'user[email]': email,
            'user[password]': password,
            'button': ''
        }
        response = rq_post(url=self.login_url, data=data, headers=self.headers)

        if '<title>Log in' in response.text:
            raise LoginError("Failed login, Check your email/password again!")
        
        return "; ".join([f"{k}={v}" for k, v in response.cookies.get_dict().items()])

# if __name__ == "__main__":
#     login = Login('email@gmail.com', 'password')
#     cookie = login.get_cookie()
#     print(cookie)