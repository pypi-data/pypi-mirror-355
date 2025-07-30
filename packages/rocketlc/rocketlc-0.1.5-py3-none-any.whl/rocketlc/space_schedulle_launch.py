from bs4 import BeautifulSoup as bs
import mechanicalsoup as mec
from rocketlc.tools_ssl import get_time
import pickle


# config cookies
cookie_file = "/tmp/cookies_ssl.pkl"
headers_file = "/tmp/headers_ssl.pkl"

br = mec.StatefulBrowser()

url_base = 'https://www.spacelaunchschedule.com'
'''
headers = {
    "authority": url_base,
    "method": "GET",
    "path": "/",
    "scheme": "https",
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
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}
'''
headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'connection': 'keep-alive', 'upgrade-insecure-requests': '1',
#            'user-agent': 'Mozilla/5.0 (Linux; Android 12; SM-A225M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'pt-BR,pt-PT;q=0.9,pt;q=0.8,en-US;q=0.7,en;q=0.6'}


try:
    with open(cookie_file, "rb") as f:
        cookies = pickle.load(f)
        br.session.cookies.update(cookies)
#        print("✅ Cookies carregados com sucesso!")

    with open(headers_file, "rb") as f:
        headers = pickle.load(f)
#        print("✅ Headers carregados com sucesso!")

except FileNotFoundError:
    print("⚠️ Cookies file not found. Building new file cookies in '.cache/'.")



#br = mec.StatefulBrowser()
br.session.headers = headers
br.session.headers.update(headers)

def launchs(page_limit:int=2)-> list:
    p = 1
    rockets = []
    for _ in range(page_limit):
        url = f'{url_base}/page/{p}/'
        url_html = br.get(url)

        # saving cookie
        with open(cookie_file, "wb") as cookie_f:
            pickle.dump(br.session.cookies, cookie_f)
        with open(headers_file, "wb") as headers_f:
            pickle.dump(br.session.headers, headers_f)

        url_html = url_html.text
        canaveral = bs(url_html,features="html.parser")
#        print(canaveral)
        div_mother = canaveral.find('div',{'class':'col-lg-8'})
        
        divs = div_mother.find_all('div')
        #print(divs)
        for dv in divs:
            if ('my-2' in dv['class']) and ('container' in dv['class']):
                #print(dv)
                name = dv.find('span',{'class':'mt-2'}).text
                mission = dv.find('h2',{'class':'h4'}).text.replace('\n','')
                mother = dv.find('h3',{'class':'h6'}).text
                
                time_usd = dv.find('time',{'class':"launchDateTime"})
                time_usd = time_usd.get('datetime',None) if time_usd else dv.find('time').get('datetime',None)
                launch_time = dv.find('time',{'class':'launchDateTime'})
                time_usd = launch_time.get('launch-window-end-utc',None) if launch_time else time_usd
                
                loc = dv.find('div',{'class':'mb-0'}).text.replace('\n','')
                
                style_a = dv.find('a',{'class':'launch-list-thumbnail'})['style']
                a_img = dv.find('a',{'class':'ezlazyload'})
              
                url_img = a_img['data-ezbg'] if a_img else style_a.split(':')[-1].split('url(')[-1].replace(')','').replace(';','').replace('//','')
                url_img = url_img.split('?')[0]

                time_launch = get_time(time_usd)
                rocket = {'name':name,
                          'mission':mission,
                          'empire':mother,
                          'datetime':time_usd,
                          'location':loc,
                          'res_seconds':time_launch['res_seconds'],
                          'hour':time_launch['hour'],
                          'date':time_launch['date'],
                          'img_url':url_img
                          }
                if time_launch['res_seconds']>0:
                    rockets.append(rocket)
                
            
        p = p+1
    
    return rockets
