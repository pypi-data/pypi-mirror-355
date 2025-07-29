from bs4 import BeautifulSoup as bs

def parse_html(html_content):
    return bs(
        html_content, 'html.parser')