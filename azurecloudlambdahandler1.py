import requests
import json
import codecs
import datetime
import boto3
import os
from decimal import Decimal
from time import sleep

def get_access_token_url(tenant_id):
    return  "https://login.microsoftonline.com/{tenantID}/oauth2/token".format(tenantID=tenant_id)

def get_rate_card_url(subscription_id, offer_id, currency_id, locale_id, region_id):
    return "https://management.azure.com:443/subscriptions/{subscriptionId}/providers/Microsoft.Commerce/RateCard?api-version=2016-08-31-preview&$filter=OfferDurableId eq '{offerId}' and Currency eq '{currencyId}' and Locale eq '{localeId}' and RegionInfo eq '{regionId}'".format(subscriptionId = subscription_id, offerId = offer_id, currencyId = currency_id, localeId = locale_id, regionId = region_id)

def upload_json_to_s3(json_data):
    bucket_name = os.environ['S3_BUCKET_NAME']
    json_file_name = "azure-" + str(datetime.date.today())+'.json'
    s3_client = boto3.resource('s3')
    s3_object = s3_client.Bucket(bucket_name).Object(json_file_name)
    s3_object.put(Body=bytes(json.dumps(json_data).encode('UTF-8')),
                  ServerSideEncryption='AES256')

def put_item_to_dynamodb(table_name, item):
    dynamodb_client = boto3.resource('dynamodb')
    table = dynamodb_client.Table(table_name)
    table.put_item(Item=item)


def put_service_item_to_db(category, name, effective_date, rate, unit, sub_category, updated_on):
    table_name = os.environ['SERVICES_TABLE_NAME']

    service_item_dict = {}
    service_item_dict['category'] = category
    service_item_dict['name'] = name
    service_item_dict['effective_date'] = effective_date
    service_item_dict['rate'] = str(rate)
    service_item_dict['unit'] = unit
    service_item_dict['sub_category'] = sub_category
    service_item_dict['updated_on'] = str(updated_on)
    service_item_dict['hash_column'] = category + ","+sub_category+","+name + "," + str(rate)

    service_item_dict = {key: value for key, value in service_item_dict.items() if value != None and value != ""}

    if (service_item_dict["hash_column"] is not None and service_item_dict["hash_column"] != ""):
        put_item_to_dynamodb(table_name, service_item_dict)

def event_handler(event, context):
    # required parameters will be retrieved from aws lambda system environment variable
    tenant_id = os.environ['AZURE_TENANT_ID']
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    client_id = os.environ['AZURE_CLIENT_ID']
    client_secret = os.environ['AZURE_CLIENT_SECRET']
    offer_id = os.environ['AZURE_OFFER_ID']

    services = ['Virtual Machines', 'Container Instances','SQL Database', 'SQL DB Edge']

    # first step is to get the token which expires every hour
    data = {
        'grant_type': (None, 'client_credentials'),
        'resource': (None, 'https://management.core.windows.net/'),
        'client_id': (None, client_id),
        'client_secret': (None, client_secret)
    }   
    response = requests.post(get_access_token_url(tenant_id), files=data)
    access_token = response.json()['access_token']
    headers =  {'Authorization': 'Bearer %s' %access_token}

    response = requests.get(get_rate_card_url(subscription_id, offer_id, 'USD', 'en-US', 'US'), headers=headers)
    response.encoding='utf-8-sig'
    services_json_data = json.loads(response.text) if response and response.status_code == 200 else None
    updated_on = datetime.date.today()
    # here we have all the service names along with their service ids
    for service in services_json_data['Meters']:
        if service.get('MeterCategory') in services:
            # for the first table, get the service name and the service id
            category = service['MeterCategory']
            name = service['MeterName']
            effective_date = service['EffectiveDate']
            rate = service['MeterRates']['0'] if '0' in service['MeterRates'] else 0
            sub_category = service['MeterSubCategory']
            unit = service['Unit']
            put_service_item_to_db(category, name, effective_date, rate, unit, sub_category, updated_on)

    return {
        "message": "Execution of the function was successful.",
        "event": event

    }
