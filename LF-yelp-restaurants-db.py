import json
import boto3
from botocore.vendored import requests
from botocore.exceptions import ClientError
from decimal import Decimal

#Getting Data from S3 to DynamoDB
s3 = boto3.resource('s3')

def insert_data(data_list, db=None, table='yelp-restaurants'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    for data in data_list:
        print(data)
        response = table.put_item(Item=data)
    print('@insert_data: response', response)
    return response


def lambda_handler(event, context):
  bucket =  'yelp-scraped-data-6998'
  key = 'yelp_data_3.json'

  obj = s3.Object(bucket, key)
  data = obj.get()['Body'].read().decode('utf-8')
  json_data = json.loads(data)

  #print(json_data)


  insert_data(json_data)

  #print(json_data)
