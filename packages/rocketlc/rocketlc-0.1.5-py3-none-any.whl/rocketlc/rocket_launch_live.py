import os
import time as tm
import pickle
from bs4 import BeautifulSoup as bs
import mechanicalsoup as mec

COOKIE_PATH = '/tmp/rocketlc_cookies.pkl'


headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.2; zh-cn; GT-I9500 Build/KOT49H)',
    'connection': 'keep-alive',
    'upgrade-insecure-requests': '1',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate',
    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}


def create_browser_with_pickle():
    br = mec.StatefulBrowser()
    br.session.headers.update(headers)

    if os.path.exists(COOKIE_PATH):
        with open(COOKIE_PATH, 'rb') as f:
            cookies = pickle.load(f)
            br.session.cookies.update(cookies)

    return br


def save_cookies(br):
    with open(COOKIE_PATH, 'wb') as f:
        pickle.dump(br.session.cookies, f)


def extract_launches_from_html(html):
    soup = bs(html, 'html.parser')
    base_launch = soup.find('div', {'class': 'launchloop'})
    divs = base_launch.find_all('div')
    rockets = []

    for div in divs:
        print(div)
        if 'row' in div.get('class', []) and 'launch' in div.get('class', []):
            try:
                date = div.find('div', {'class': 'launch_date'}).text
                time_ = div.find('div', {'class': 'launch_time'}).text
                rocket_name = div.find('div', {'class': 'rlt-vehicle'}).text
                mother_rocket = div.find('div', {'class': 'rlt-provider'}).text
                loc_launch = div.find('div', {'class': 'rlt-location'}).text
                mission = div.find('div', {'class': 'mission_name'}).text

                rocket_series = None
                if mother_rocket == 'SpaceX':
                    tag = div.find('div', {'class': 'launch_tag'})
                    if tag:
                        rocket_series = tag.text

                rocket = {
                    'mission': mission.strip(),
                    'date_launch': date.strip(),
                    'time_launch': time_.strip(),
                    'name': rocket_name.strip(),
                    'empire': mother_rocket.strip(),
                    'location': loc_launch.strip(),
                    'series': rocket_series
                }
                rockets.append(rocket)
            except (AttributeError, KeyError, TypeError):
                continue
    return rockets


def past_launchs():
    br = create_browser_with_pickle()
    html = br.get("https://www.rocketlaunch.live/?pastOnly=1").text
    save_cookies(br)

    time_init = tm.time()
    rockets = extract_launches_from_html(html)
    ping = tm.time() - time_init

    return {'ping': ping, 'len_videos': len(rockets), 'rockets': rockets}


def future_launchs():
    br = create_browser_with_pickle()
    html = br.get("https://www.rocketlaunch.live/").text
    save_cookies(br)

    time_init = tm.time()
    rockets = extract_launches_from_html(html)
    ping = tm.time() - time_init

    return {'ping': ping, 'len_videos': len(rockets), 'rockets': rockets}
