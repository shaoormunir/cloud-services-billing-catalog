import requests
import json
import boto3
import os
import datetime

catalog_url = 'https://globalcatalog.cloud.ibm.com/api/v1'




def get_pricing_api_url(id):
    return "https://globalcatalog.cloud.ibm.com/api/v1/{}/pricing".format(id)

def upload_json_to_s3(json_data, service_name):
    bucket_name = os.environ['S3_BUCKET_NAME']
    json_file_name = service_name + '-' + str(datetime.date.today())+'.json'
    s3_client = boto3.resource('s3')
    s3_object = s3_client.Bucket(bucket_name).Object(json_file_name)
    s3_object.put(Body=bytes(json.dumps(json_data).encode('UTF-8')),
                  ServerSideEncryption='AES256')

def put_item_to_dynamodb(table_name, item):
    dynamodb_client = boto3.resource('dynamodb')
    table = dynamodb_client.Table(table_name)
    table.put_item(Item=item)

def put_service_item_to_db(service_id, service_name):
    table_name = os.environ['SERVICES_TABLE_NAME']

    service_item_dict = {}
    service_item_dict['service_id'] = service_id
    service_item_dict['service_name'] = service_name

    put_item_to_dynamodb(table_name, service_item_dict)


def event_handler(event, context):
    params ={'account':'global', 'include':'*', 'sorty-by':'name', 'descending':'false', 'languages': 'en-us', 'complete':'false'}
    headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
    
    response = requests.get(url=catalog_url, params=params, headers=headers)

    resources_json_data = response.json(
    ) if response and response.status_code == 200 else None

    pricing_json_data = None
    headers = { 'accept': "application/json" }
    params = {'account':'global'}

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