import requests
import json

catalog_url = 'https://globalcatalog.cloud.ibm.com/api/v1'

headers = {'Content-Type': 'application/json', 'accept': 'application/json'}

params ={'account':'global', 'include':'*', 'sorty-by':'name', 'descending':'false', 'languages': 'en-us', 'complete':'false'}

r = requests.get(url=catalog_url, params=params, headers=headers)

# with open ('ibmcloud.json', 'w') as f:
#     json.dump(r.json(), f)

pricing_json_data = None
headers = { 'accept': "application/json" }
params = {'account':'global'}

pricing_url = "https://globalcatalog.cloud.ibm.com/api/v1/{}/pricing"
resource_prices = dict()

for resource in r.json()['resources']:
    #check if the url has any children
    children_url = resource['children_url']

    resource_id = resource['id']
    print("Checking id {}".format(resource_id))
    
    r = requests.get(url=url, params=params, headers=headers)
    if(pricing_json_data is None):
        pricing_json_data = r.json()
    else:
        pricing_json_data.update(r.json())

with open ('ibmcloudpricing.json', 'w') as f:
    json.dump(pricing_json_data, f)


def rec_get_resource_price(url, resource_prices):
    headers = headers = { 'accept': "application/json" }
    response = requests.get(url=url, headers=headers)
    children_url = response.json()['children_url']
    if(check_if_child_exist(children_url)):
        rec_get_resource_price(children_url, resource_prices)
    else:
        pricing_response = requests.get(url=pricing_url.format(response.json()['id']))


def check_if_child_exist(url):
    headers = headers = { 'accept': "application/json" }
    response = requests.get(url=url, headers=headers)
    return response.json()['count'] == 0