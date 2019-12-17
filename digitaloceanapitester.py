import requests
import json

token = '1aa0fc6167681d40e2a53390eec17725992f8cea4e630a0db53e08bc4d78e6ae'

url = 'https://api.digitalocean.com/v2/sizes'

headers = {'Authorization':'Bearer '+ token, 'Content-Type':'application/json'}

r = requests.get(url=url, headers=headers)

with open("digitalocean.json", 'w') as f:
    json.dump(r.json(), f)
