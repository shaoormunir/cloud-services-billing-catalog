import requests
import json
import datetime
import boto3
import os
from decimal import Decimal


def get_service_list_api_url(api_key):
    return 'https://cloudbilling.googleapis.com/v1/services?key=' + api_key


def get_service_info_api_url(api_key, service_id):
    return 'https://cloudbilling.googleapis.com/v1/services/' + service_id + '/skus?key='+api_key


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


def put_sku_item_to_db(service_id, sku_id, sku_description, effective_time):
    table_name = os.environ['SKUS_TABLE_NAME']

    sku_item_dict = {}
    sku_item_dict['sku_id'] = sku_id
    sku_item_dict['service_id'] = service_id
    sku_item_dict['description'] = sku_description
    sku_item_dict['effective_time'] = effective_time

    put_item_to_dynamodb(table_name, sku_item_dict)


def put_tiered_rate_item_to_db(sku_id, start_usage_amount, units, nanos, currency, formatted_price, updated_on):
    table_name = os.environ['RATES_TABLE_NAME']

    tiered_rate_item_dict = {}
    tiered_rate_item_dict['sku_id'] = sku_id
    tiered_rate_item_dict['start_usage_amount'] = start_usage_amount
    tiered_rate_item_dict['units'] = units
    tiered_rate_item_dict['nanos'] = nanos
    tiered_rate_item_dict['currency'] = currency
    tiered_rate_item_dict['formatted_price'] = Decimal(str(formatted_price))
    tiered_rate_item_dict['updated_on'] = str(updated_on)

    put_item_to_dynamodb(table_name, tiered_rate_item_dict)


def event_handler(event, context):
    # api will be retrieved from aws lambda system environment variable
    api_key = os.environ['GOOGLE_CLOUD_API_KEY']

    compute_services = ['Compute Engine', 'Kubernetes Engine',
                        'Cloud Run', 'App Engine', 'Cloud Functions']
    storage_services = ['Cloud Storage', 'Persistent Disk',
                        'Cloud Filestore', 'Data Transfer Services', 'Drive Enterprise']
    other_services = []

    # first step is to get the list of all Google Cloud services
    response = requests.get(get_service_list_api_url(api_key))

    services_json_data = response.json(
    ) if response and response.status_code == 200 else None

    updated_on = datetime.date.today()
    print(updated_on)

    # here we have all the service names along with their service ids
    for service in services_json_data['services']:
        if service.get('displayName') in compute_services or service.get('displayName') in storage_services or service.get('displayName') in other_services:
            # for the first table, get the service name and the service id
            service_name = service.get('displayName')
            service_id = service.get('serviceId')

            put_service_item_to_db(service_id, service_name)

            response = requests.get(get_service_info_api_url(
                api_key, service.get('serviceId')))

            service_json_data = response.json()

            upload_json_to_s3(service_json_data, service_name)

            for sku in service_json_data['skus']:
                # for the second table, get the sku id, the sku description

                sku_id = sku.get('skuId')
                sku_description = sku.get('description')
                print(sku_description)
                pricing_info = sku['pricingInfo'][0]
                effective_time = pricing_info['effectiveTime']
                print(effective_time)

                put_sku_item_to_db(service_id, sku_id,
                                   sku_description, effective_time)

                for tiered_rate in pricing_info['pricingExpression']['tieredRates']:
                    # for the third table, get the price, currency, and it will also store upadtion date

                    start_usage_amount = tiered_rate['startUsageAmount']
                    units = tiered_rate['unitPrice']['units']
                    nanos = tiered_rate['unitPrice']['nanos']
                    print(units)
                    print(nanos)
                    currency = tiered_rate['unitPrice'].get('currencyCode')
                    formatted_price = int(units, 10) + nanos/1000000000

                    print(currency)
                    print("formatted price is = {:.10f} ".format(
                        formatted_price))

                    put_tiered_rate_item_to_db(
                        sku_id, start_usage_amount, units, nanos, currency, formatted_price, updated_on)

    return {
        "message": "Execution of the function was successful.",
        "event": event

    }
