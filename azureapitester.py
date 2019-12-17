import requests
import json
# this portion is testing the azure api for getting data about services


azure_directory_id = 'd648dc39-0da3-4fee-b5f4-8fcbd4967894'
azure_subscription_id = '196cc768-c915-4ab5-83bc-d54614e69964'

import requests
 
# Parameters need for API
subscription = '196cc768-c915-4ab5-83bc-d54614e69964'
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkJCOENlRlZxeWFHckdOdWVoSklpTDRkZmp6dyIsImtpZCI6IkJCOENlRlZxeWFHckdOdWVoSklpTDRkZmp6dyJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9kNjQ4ZGMzOS0wZGEzLTRmZWUtYjVmNC04ZmNiZDQ5Njc4OTQvIiwiaWF0IjoxNTc1NzU0MjgxLCJuYmYiOjE1NzU3NTQyODEsImV4cCI6MTU3NTc1ODE4MSwiYWlvIjoiNDJWZ1lMQi9lZHpZYUpQdWdmcjdxeGJ6K1Y1NEFnQT0iLCJhcHBpZCI6IjY0MzgzMzNhLTUwMjItNGM4OC1hZjA1LTBlYjFmZGU1N2UwZiIsImFwcGlkYWNyIjoiMSIsImlkcCI6Imh0dHBzOi8vc3RzLndpbmRvd3MubmV0L2Q2NDhkYzM5LTBkYTMtNGZlZS1iNWY0LThmY2JkNDk2Nzg5NC8iLCJvaWQiOiJiNzJlN2U5Mi0zNWFkLTQ5OWUtOWUzYi04MDE2ZmYzMmU5ZmIiLCJzdWIiOiJiNzJlN2U5Mi0zNWFkLTQ5OWUtOWUzYi04MDE2ZmYzMmU5ZmIiLCJ0aWQiOiJkNjQ4ZGMzOS0wZGEzLTRmZWUtYjVmNC04ZmNiZDQ5Njc4OTQiLCJ1dGkiOiI5RHJlTXBORkFrUzhHZTVNcGtPSkFRIiwidmVyIjoiMS4wIn0.KMbRiGVh2McZPpK7wPGi2wgZONcs2fhyt4r4j9cvmJCRtT2xFH3tSs4gClZXHM_J5VcjPCPNbnLjYBqjhLMwsLsvbiBp2KaGvTkiNXnh1gp3UtuqkgzEbUnHt503pzqAUa7J9iEIx0o6Ed4fqhAgYEfVzO_v2ZDwNCwwb5X607MfMlEelXUuZGK9dxXPEtssPsn-5JITb_W3FL7fJuT-a152GNZVp_m81TOnwaV-9bgUMIWLQq3uTr8l4RpwEu5IHI-GEQzj6NcNcFmK0W4anHKCA9lTyvfJ25KHBPsSKHJFoVM6vNdvDGHKmJoSI1udJiYLdxEB3T0zedErjQSgmQ'
offer = 'MS-AZR-0003P'
currency = 'USD'
locale = 'en-US'
region = 'US'
rateCardUrl = "https://management.azure.com:443/subscriptions/{subscriptionId}/providers/Microsoft.Commerce/RateCard?api-version=2016-08-31-preview&$filter=OfferDurableId eq '{offerId}' and Currency eq '{currencyId}' and Locale eq '{localeId}' and RegionInfo eq '{regionId}'".format(subscriptionId = subscription, offerId = offer, currencyId = currency, localeId = locale, regionId = region)

# Don't allow redirects and call the RateCard API
response = requests.get(rateCardUrl, headers = {'Authorization': 'Bearer %s' %token})

json_data = response.json()

meter_catagory_list = set()

for meter in json_data['Meters']:
  meter_catagory_list.add(meter['MeterCategory'])