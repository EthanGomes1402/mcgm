import time
import requests

page = ''
while page == '':
    try:
        page = requests.get("https://swm.vtms.cleanupmumbai.com")
        break
    except Exception as e:
        print("Connection refused by the server..")
        print(str(e))
        print("Let me sleep for 5 seconds")
        print("ZZzzzz...")
        time.sleep(5)
        print("Was a nice sleep, now let me continue...")
        continue
