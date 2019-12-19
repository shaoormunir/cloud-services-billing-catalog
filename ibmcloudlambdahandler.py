import requests
import json
import boto3
import os
import datetime

def get_pricing_api_url(id):
    return "https://globalcatalog.cloud.ibm.com/api/v1/{}/pricing".format(id)

def get_global_catalog_url():
    return 'https://globalcatalog.cloud.ibm.com/api/v1'

def get_pricing_kinds():
    return ['buildpack', 'service', 'ssm-service', 'application', 'plan', 'deployment']

def get_headers():
    return {'Content-Type': 'application/json', 'accept': 'application/json'}

def get_global_params():
    return  {'account':'global', 'include':'*', 'sorty-by':'name', 'descending':'false', 'languages': 'en-us', 'complete':'false'}

def upload_json_to_s3(json_data, resource_name):
    bucket_name = os.environ['S3_BUCKET_NAME']
    json_file_name = "ibmcloud-" + resource_name + '-' + str(datetime.date.today())+'.json'
    s3_client = boto3.resource('s3')
    s3_object = s3_client.Bucket(bucket_name).Object(json_file_name)
    s3_object.put(Body=bytes(json.dumps(json_data).encode('UTF-8')),
                  ServerSideEncryption='AES256')

def put_item_to_dynamodb(table_name, item):
    dynamodb_client = boto3.resource('dynamodb')
    table = dynamodb_client.Table(table_name)
    table.put_item(Item=item)

def put_resource_item_to_db(resource_id, resource_name, resource_display_name):
    table_name = os.environ['RESOURCES_TABLE_NAME']

    resource_item_dict = {}
    resource_item_dict['resource_id'] = resource_id
    resource_item_dict['resource_name'] = resource_name
    resource_item_dict['resource_display_name'] = resource_display_name

    put_item_to_dynamodb(table_name, resource_item_dict)

def put_plan_item_to_db(resource_id, plan_id, plan_name, plan_display_name):
    table_name = os.environ['PLANS_TABLE_NAME']

    plan_item_dict = {}
    plan_item_dict['resource_id'] = resource_id
    plan_item_dict['plan_id'] = plan_id
    plan_item_dict['plan_name'] = plan_name
    plan_item_dict['plan_display_name'] = plan_display_name

    put_item_to_dynamodb(table_name, plan_item_dict)

def put_price_metric_item_to_db(plan_id, price_metric_id, charge_unit_display_name, charge_unit_name, charge_unit, charge_unit_quantity):
    table_name = os.environ['PRICE_METRICS_TABLE_NAME']

    price_metric_item_dict = {}
    price_metric_item_dict['plan_id'] = plan_id
    price_metric_item_dict['price_metric_id'] = price_metric_id
    price_metric_item_dict['charge_unit_display_name'] = charge_unit_display_name if charge_unit_display_name != '' else "N/A"
    price_metric_item_dict['charge_unit_name'] = charge_unit_name if charge_unit_name != '' else "N/A"
    price_metric_item_dict['charge_unit'] = charge_unit if charge_unit != '' else "N/A"
    price_metric_item_dict['charge_unit_quantity'] = str(charge_unit_quantity)

    put_item_to_dynamodb(table_name, price_metric_item_dict)


def put_price_item_to_db(price_metric_id,quantity_tier, price, updated_on):
    table_name = os.environ['PRICES_TABLE_NAME']

    price_item_dict = {}
    price_item_dict['price_metric_id'] = price_metric_id
    price_item_dict['quantity_tier'] = str(quantity_tier)
    price_item_dict['price'] = str(price)
    price_item_dict['updated_on'] = str(updated_on)
    price_item_dict['hash_column'] = price_metric_id + "," + str(quantity_tier) + "," + str(price)

    put_item_to_dynamodb(table_name, price_item_dict)


def event_handler(event, context):
    response = requests.get(url=get_global_catalog_url(), params=get_global_params(), headers=get_headers())

    resource_required = ['BigInsights for Apache Hadoop (Subscription)', 'Block Storage', 'Blockchain Platform', 'box', 'bwlosbbroker-service', 'Compute 8x16', 'Compute 16x32 - VPC on Classic', 'Compute 2x4 - VPC on Classic', 'Compute 32x64 - VPC on Classic', 'Compute 4x8 - VPC on Classic', 'Compute 8x16 - VPC on Classic', 'Compose for MySQL', 'Compose for RethinkDB', 'Compose for ScyllaDB', 'Compute 16x32 - VPC Gen2', 'Compute 2x4 - VPC Gen2', 'Compute 32x64 - VPC Gen2', 'Compute 4x8 - VPC Gen2', 'Compute 8x16 - VPC Gen2', 'Db2 Warehouse', 'Db2', 'Databases for Elasticsearch', 'Databases for etcd', 'Databases for MongoDB', 'Databases for PostgreSQL', 'Databases for Redis', 'Db2 Hosted', 'Hyper Protect DBaaS for MongoDB', 'Hyper Protect DBaaS for PostgreSQL', 'IBM Cloud Secure Virtualization', 'Memory 4x32', 'Managed Backup Services', 'Managed Disaster Recovery Services', 'Mass Data Migration', 'Memory 16x128 - VPC on Classic', 'Memory 2x16 - VPC on Classic', 'Memory 32x256 - VPC on Classic', 'Memory 4x32 - VPC on Classic', 'Memory 8x64 - VPC on Classic', 'Memory 16x128 - VPC Gen2', 'Memory 2x16 - VPC Gen2', 'Memory 32x256 - VPC Gen2', 'Memory 4x32 - VPC Gen2', 'Memory 8x64 - VPC Gen2', 'Object Storage', 'Virtual Server']
    resources_json_data = response.json(
    ) if response and response.status_code == 200 else None
    while True:
        for resource in resources_json_data['resources']:
            if resource['overview_ui']['en']['display_name'] in resource_required:
                resource_dict = {}
                resource_dict['name'] = resource['name']
                resource_dict['display_name'] = resource['overview_ui']['en']['display_name']
                resource_dict['resource_id'] = resource['id']
                rec_get_resource_price(resource, resource_dict)
        if 'next' not in resources_json_data:
            break
        break
        next_url = resources_json_data["next"]
        response = requests.get(url=next_url, params=get_global_params(), headers=get_headers())
        resources_json_data = response.json() if response and response.status_code == 200 else None

def rec_get_resource_price (resource, resource_dict):
    headers = { 'accept': "application/json" }
    params = {'account':'global'}
    if check_if_resource_has_children(resource):
        children_url = resource['children_url']
        response = requests.get(url=children_url, headers=headers, params=params)
        resources_json_data = response.json() if response and response.status_code == 200 else None
        for resource in resources_json_data['resources']:
            resource_dict['plan_name'] = resource['name']
            resource_dict['plan_display_name'] = resource['overview_ui']['en']['display_name']
            resource_dict['plan_id'] = resource['id']
            rec_get_resource_price(resource, resource_dict)
    else:
        pricing_response = requests.get(get_pricing_api_url(resource['id']), headers=headers)
        pricing_json_data = pricing_response.json() if pricing_response and pricing_response.status_code == 200 else None
        if pricing_json_data is not None and pricing_json_data['metrics'] is not None:
            for metric in pricing_json_data['metrics']:

                put_resource_item_to_db(resource_dict['resource_id'], resource_dict['name'], resource_dict['display_name'])

                put_plan_item_to_db(resource_dict['resource_id'], resource_dict['plan_id'],resource_dict['plan_name'], resource_dict['plan_display_name'])

                put_price_metric_item_to_db(resource_dict['plan_id'], metric['metric_id'], metric['charge_unit_display_name'],metric['charge_unit_name'], metric['charge_unit'], metric['charge_unit_quantity'])

                if metric['amounts'] is not None:
                    for amount in metric['amounts']:
                        if amount['country'] == 'USA':
                            for price in amount['prices']:
                                print("Price Tier: {}, Price: {}".format(price['quantity_tier'], price['price']))
                                put_price_item_to_db(metric['metric_id'], price['quantity_tier'], price['price'], datetime.date.today())

def check_if_resource_has_children(resource):
    children_url = resource['children_url']
    response = requests.get(url=children_url, headers=get_headers())
    return response.json()['count'] > 0

event_handler(None, None)