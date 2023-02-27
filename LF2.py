import json
import os
import boto3
from random import randint
import ast

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Create SQS client
from botocore.exceptions import ClientError
sqs = boto3.client('sqs')
sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/134022936267/diningsqs"
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')
ses = boto3.client('ses')

REGION = 'us-east-1'
HOST = 'search-restaurants-k4l2batx4shvhgs6r2nmk6dgnu.us-east-1.es.amazonaws.com'
INDEX = 'restaurants'

def lambda_handler(event, context):
    attributes, receipt_handle = receive_message()
    elastic_query_results = query(attributes['Cuisine'])
    rand_result1 = elastic_query_results[randint(0,17)]
    rand_result2 = elastic_query_results[randint(18,33)]
    rand_result3 = elastic_query_results[randint(34,49)]

    id_val1 = rand_result1['id']
    id_val2 = rand_result2['id']
    id_val3 = rand_result3['id']

    recommendation1 = lookup_data({'id': id_val1})
    recommendation2 = lookup_data({'id': id_val2})
    recommendation3 = lookup_data({'id': id_val3})

    SES_message = send_SES_message(attributes, recommendation1, recommendation2, recommendation3)
    delete_message(receipt_handle)
    delete_message(receipt_handle)
    return SES_message

def receive_message():
    resp = sqs.receive_message(
            QueueUrl=sqs_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )

    message_body = resp['Messages'][0]['Body']
    message_body_dict = ast.literal_eval(message_body)
    dict_attributes = parse_attributes(message_body_dict)
    return dict_attributes, resp['Messages'][0]['ReceiptHandle']

def parse_attributes(message_attributes):
    print(message_attributes["Cuisine"]["value"]["interpretedValue"])
    dict_attributes = {"Cuisine": message_attributes["Cuisine"]["value"]["interpretedValue"],
            "DiningDate": message_attributes["date"]["value"]["interpretedValue"],
            "DiningTime": message_attributes["time"]["value"]["interpretedValue"],
            "Location": message_attributes["City"]["value"]["interpretedValue"],
            "NumberOfPeople": message_attributes["number-of-people"]["value"]["interpretedValue"],
            "Email": message_attributes["email"]["value"]["interpretedValue"],
    }
    return dict_attributes

# if set up ElasticSearch: use the cuisine type to get a random business_id
# then use this method to search using that key
def lookup_data(key, db=None, table='yelp-restaurants'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    try:
        response = table.get_item(Key=key)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print(response['Item'])
        return response['Item']

def query(term):
    q = {'size': 50, 'query': {'multi_match': {'query': term}}}
    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)
    res = client.search(index=INDEX, body=q)
    #print(res)
    hits = res['hits']['hits']
    results = []
    for hit in hits:
        results.append(hit['_source'])
    return results

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)

def send_SES_message(attributes, recommendation1, recommendation2, recommendation3):
    m1 = f"Hello! Here are my {attributes['Cuisine']} restaurant suggestions for {attributes['NumberOfPeople']} people, for {attributes['DiningDate']} at {attributes['DiningTime']}: "
    m2 = f"1. {recommendation1['name']}, located at {recommendation1['location']} which has a rating of {recommendation1['rating']}. "
    m3 = f"2. {recommendation2['name']}, located at {recommendation2['location']} which has a rating of {recommendation2['rating']}. "
    m4 = f"3. {recommendation3['name']}, located at {recommendation3['location']} which has a rating of {recommendation3['rating']}. "
    m5 = f"Enjoy your meal!"

    SES_message = m1+m2+m3+m4+m5
    # print(accepted_phone)
    # Send the recommendation message to the phone number using SNS

    ses.send_email(
                    Source='sidvijay20@gmail.com',
                    Destination={
                        'ToAddresses': [
                            attributes['Email']
                        ]
                    },
                    Message={
                        'Subject': {
                            'Data': 'Restaurant Recommendations'
                        },
                        'Body': {
                            'Text': {
                                'Data': SES_message
                            }
                        }
                    })

    # print("phone number: ")
    print(attributes['Email'])
    return SES_message

def delete_message(receipt_handle):
    resp = sqs.delete_message(
            QueueUrl=sqs_queue_url,
            ReceiptHandle=receipt_handle
        )
    #print(resp)
    return resp
    
