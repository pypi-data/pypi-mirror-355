from bs4 import BeautifulSoup as bs
import mechanicalsoup as mec
import cssutils as css
import time as tm
#from rocketlc.tools_ssl import get_time
import os
import pickle
import re

# config cookies
cookie_file = "/tmp/cookies_nsf.pkl"
headers_file = "/tmp/headers_nsf.pkl"

br = mec.StatefulBrowser()


url_base = "https://nextspaceflight.com"
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.6",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version-list": '"Brave";v="131.0.0.0", "Chromium";v="131.0.0.0", "Not_A Brand";v="24.0.0.0"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Linux"',
    "sec-ch-ua-platform-version": '"6.11.2"',
    "sec-ch-ua-wow64": "?0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


try:
    with open(cookie_file, "rb") as f:
        cookies = pickle.load(f)
        br.session.cookies.update(cookies)
#        print("✅ Cookies carregados com sucesso!")

    with open(headers_file, "rb") as f:
        headers = pickle.load(f)
#        print("✅ Headers carregados com sucesso!")

except FileNotFoundError:
    print("⚠ Cookies file not found. Building new file cookies in '.cache/'.")



br.session.headers = headers
br.session.headers.update(headers)


def get_launchs():
    response = br.get(url_base+'/launches')
    nsf = bs(response.text,features="html.parser")
    div_main = nsf.find("div",{"class":"mdl-grid"})
#print(div_main)
    div_rockets = div_main.find_all("div", {'class':'mdl-cell mdl-cell--6-col'})

#print(len(div_rockets))
#print(div_rockets[0])
    i = 0
    rockets = []
    for rocket in div_rockets:
        rocket_dict = {}

        rocket_dict['url'] = url_base + rocket.find('a')['href']
        rocket_dict['empire'] = rocket.find("div",{"class":"mdl-card__title-text"}).find("span").text
        rocket_dict['name'],rocket_dict['mission'] = tuple(rocket.find("h5",{"class":"header-style"}).text.split("|"))

        rocket_dict['thumbnail'] = rocket.find_all('style')[0].get_text().split('background: ')[1].split('url(')[1].split(')')[0]
    
        date = rocket.find("div",{"class":"mdl-card__supporting-text"}).find("span")
        if not date :
            rocket_dict['date'],rocket_dict['location'] = tuple(rocket.find("div",{"class":"mdl-card__supporting-text"}).decode_contents().split('<br/>'))
        else:
            rocket_dict['date'] = rocket.find("div",{"class":"mdl-card__supporting-text"}).find("span").text
            rocket_dict['location'] = rocket.find("div",{"class":"mdl-card__supporting-text"}).decode_contents().split('<br/>')[1]

        for key,value in rocket_dict.items():
            rocket_dict[key] = re.sub(r"\s+", " ", value).strip()
        rockets.append(rocket_dict)

    with open(cookie_file, "wb") as f:
        pickle.dump(br.session.cookies, f)
    with open(headers_file, "wb") as f:
        pickle.dump(br.session.headers, f)
    
    return rockets
