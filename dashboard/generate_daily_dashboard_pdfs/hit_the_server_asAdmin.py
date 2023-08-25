import requests
import os
import ssl


#headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
#'Upgrade-Insecure-Requests': '1',
#'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
#'Accept-Encoding': 'gzip, deflate, br',
#'Accept-Language': 'en-US,en;q=0.9',
#'Connection': 'keep-alive',
#'Host': 'swm.vtms.cleanupmumbai.com',
#'sec-ch-ua': """\"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99\"""",
#'sec-ch-ua-mobile': '?0',
#'Sec-Fetch-Dest': 'document',
#'Sec-Fetch-Mode': 'navigate',
#'Sec-Fetch-Site': 'none',
#'Sec-Fetch-User': '?1'
#}

headers = requests.utils.default_headers()
headers.update(
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    })

client = requests.session()

abc = client.get("https://swm.vtms.cleanupmumbai.com/accounts/login", verify=False)

print(str(abc.text))
csrftoken = abc.cookies['csrftoken']
print(csrftoken)


login_data = {'username':"swm",
    'password':"swm", 
    'csrfmiddlewaretoken':csrftoken,
    'next': '/swm/latest_vehicle_status/'}

r1=client.post("https://swm.vtms.cleanupmumbai.com/accounts/login/",data=login_data)



#print(str(r1))





#os.system("/home/mcgm/Development/mcgm/menv/bin/python3 /home/mcgm/Development/mcgm/mcgm/dashboard/generate_daily_dashboard_pdfs/generatepdf.py")
