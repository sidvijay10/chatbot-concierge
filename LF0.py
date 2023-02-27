import boto3
import json

# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    msg_from_user = event['messages'][0]
    # Initiate conversation with Lex
    response = client.recognize_text(
            botId='AIBWO8BTNC', # MODIFY HERE
            botAliasId='J9TSLWEPPL', # MODIFY HERE
            localeId='en_US',
            sessionId='testuser',
            text=msg_from_user['unstructured']['text'])

    msg_from_lex = response.get('messages', [])

    output = []
    if msg_from_lex:
        message = {
            'type': 'unstructured',
            'unstructured': {
                'id': response['ResponseMetadata']['RequestId'],
                'text': msg_from_lex[0]['content'],
                'date': response['ResponseMetadata']['HTTPHeaders']['date']
            }
        }
        output.append(message)
    resp = {
        'statusCode': 200,
        'messages': output
    }
    return resp
