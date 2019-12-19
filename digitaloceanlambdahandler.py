import requests
import json
import datetime
import boto3
import os
from decimal import Decimal

def get_next_page_url(json_response):
    return json_response["links"]["pages"]["next"] if 'next' in json_response["links"]["pages"] else None

def upload_json_to_s3(json_data, page_number):
    bucket_name = os.environ['S3_BUCKET_NAME']
    json_file_name = "digitalocean_droplet-" + page_number + '-' + str(datetime.date.today())+'.json'
    s3_client = boto3.resource('s3')
    s3_object = s3_client.Bucket(bucket_name).Object(json_file_name)
    s3_object.put(Body=bytes(json.dumps(json_data).encode('UTF-8')),
                  ServerSideEncryption='AES256')

def put_item_to_dynamodb(table_name, item):
    dynamodb_client = boto3.resource('dynamodb')
    table = dynamodb_client.Table(table_name)
    table.put_item(Item=item)

def put_droplet_item_to_db(slug, memory, vcpus, disk, transfer, price_monthly, price_hourly, updated_on):
    table_name = os.environ['DROPLET_TABLE_NAME']

    droplet_item_dic = {}
    droplet_item_dic['slug'] = slug
    droplet_item_dic['memory'] = memory
    droplet_item_dic['vcpus'] = vcpus
    droplet_item_dic['disk'] = disk
    droplet_item_dic['transfer'] = transfer
    droplet_item_dic['price_monthly'] = price_monthly
    droplet_item_dic['price_hourly'] = price_hourly
    droplet_item_dic['updated_on'] = updated_on

    put_item_to_dynamodb(table_name, droplet_item_dic)

def event_handler(event, context):
    # token to authenticate with the digital ocean API, set in the lambda environment variables
    token = os.environ['DIGITAL_OCEAN_AUTH_TOKEN']
    #token = '1aa0fc6167681d40e2a53390eec17725992f8cea4e630a0db53e08bc4d78e6ae'
    
    # base url that will be hit first
    base_url = 'https://api.digitalocean.com/v2/sizes'

    # header will be passed with the request to authenticate
    headers = {'Authorization':'Bearer '+ token, 'Content-Type':'application/json'}

    response = requests.get(url=base_url, headers=headers)

    droplet_json_data = response.json(
    ) if response and response.status_code == 200 else None

    updated_on = datetime.date.today()
    print(updated_on)
    page_number = 1

    while True and droplet_json_data is not None:
        upload_json_to_s3(droplet_json_data, page_number)
        page_number+=1
        for size in droplet_json_data['sizes']:
            slug = size['slug']
            memory = size['memory']
            vcpus = size['vcpus']
            disk = size['disk']
            transfer = size['transfer']
            price_monthly = size['price_monthly']
            price_hourly = size['price_hourly']
            put_droplet_item_to_db(slug, memory, vcpus, disk, transfer, price_monthly, price_hourly, updated_on)
        base_url =get_next_page_url(droplet_json_data)
        break
        if base_url == None:
            break
        else:
            response = requests.get(url=base_url, headers=headers)
            droplet_json_data = response.json() if response and response.status_code == 200 else None
            
    return {
        "message": "Execution of the function was successful.",
        "event": event
    }