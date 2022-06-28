import requests
import os


client = requests.session()
client.get("http://swm.vtms.cleanupmumbai.com/accounts/login/")
csrftoken = client.cookies['csrftoken']

login_data = {'username':"swm",
    'password':"swm", 
    'csrfmiddlewaretoken':csrftoken,
    'next': '/swm/latest_vehicle_status/'}

r1=client.post("http://swm.vtms.cleanupmumbai.com/accounts/login/",data=login_data)



print(str(r1))





os.system("/home/mcgm/Development/mcgm/menv/bin/python3 /home/mcgm/Development/mcgm/mcgm/dashboard/generate_daily_dashboard_pdfs/generatepdf.py")
