import json
import boto3

cuisines = ['mexican', 'italian', 'korean', 'indian', 'chinese']

#source for validating template: https://github.com/CumulusCycles/Amazon_Lex_demo/blob/main/Lambda/lambda_handler.py

def validate_order(slots):
    # Validate City
    if not slots['City']:
        print('Validating City')

        return {
            'isValid': False,
            'invalidSlot': 'City'
        }

    # Validate Cuisine
    if not slots['Cuisine']:
        print('Validating Cuisine')

        return {
            'isValid': False,
            'invalidSlot': 'Cuisine'
        }

    if slots['Cuisine']['value']['interpretedValue'].lower() not in cuisines:
        print('cuisine is not supported')

        return {
            'isValid': False,
            'invalidSlot': 'Cuisine',
            'message': 'Sorry, this cuisine is not available. Please try another one!'
        }

    # Validate Number of People
    if not slots['number-of-people']:
        print('Validating number-of-people')

        return {
            'isValid': False,
            'invalidSlot': 'number-of-people'
        }

    if int(slots['number-of-people']['value']['interpretedValue']) < 1:
        print('number-of-people less than or equal to 0')

        return {
            'isValid': False,
            'invalidSlot': 'number-of-people',
            'message': 'Please select a party size above 0!'
        }

    # Validate Date
    if not slots['date']:
        print('Validating Date')

        return {
            'isValid': False,
            'invalidSlot': 'date'
        }

    print(slots['date'])

    import datetime

    def date_possible(date_lex):
        try:
            date = datetime.datetime.strptime(date_lex, '%Y-%m-%d').date()
            present = datetime.date.today() - datetime.timedelta(days=1)
            if date < present:
                return False
            else:
                return True
        except ValueError:
            return False


    if not date_possible(slots['date']['value']['interpretedValue']):
        print('date not possible')

        return {
            'isValid': False,
            'invalidSlot': 'date',
            'message': 'Oops! That date is in the past. Please choose a valid date!'
        }

    # Validate Time
    if not slots['time']:
        print('Validating Time')

        return {
            'isValid': False,
            'invalidSlot': 'time'
        }

    # Validate Email
    if not slots['email']:
        print('Validating email')

        return {
            'isValid': False,
            'invalidSlot': 'email'
        }

    # Valid Order
    return {'isValid': True}


def dining_intent(event, context):
    #print(event)

    bot_name = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent_name = event['sessionState']['intent']['name']

    order_validation_result = validate_order(slots)

    if event['invocationSource'] == 'DialogCodeHook':
        if not order_validation_result['isValid']:
            if 'message' in order_validation_result:
                response = {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": order_validation_result['invalidSlot'],
                            "type": "ElicitSlot"
                        },
                        "intent": {
                            "name": intent_name,
                            "slots": slots
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": order_validation_result['message']
                        }
                    ]
                }
            else:
                response = {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": order_validation_result['invalidSlot'],
                            "type": "ElicitSlot"
                        },
                        "intent": {
                            "name": intent_name,
                            "slots": slots
                        }
                    }
                }
        else:
            response = {
                "sessionState": {
                    "dialogAction": {
                        "type": "Delegate"
                    },
                    "intent": {
                        'name': intent_name,
                        'slots': slots
                    }
                }
            }

            # Send to SQS queue
            user_input = event['sessionState']['intent']['slots']
            sqs = boto3.client('sqs', region_name='us-east-1')
            queue_url = "https://sqs.us-east-1.amazonaws.com/134022936267/diningsqs"
            response_sqs = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(user_input))

            print("SENT TO QUEUE")
            print(event)


    if event['invocationSource'] == 'FulfillmentCodeHook':
        response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": intent_name,
                    "slots": slots,
                    "state": "Fulfilled"
                }

            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "You’re all set. Expect my suggestions shortly! Have a good day."
                }
            ]
        }

    #print(response)
    return response


def thankyou_intent(event, context):

    session = event['sessionState']
    content = "You’re welcome."

    response = {
        "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": "ThankYouIntent",
                    "state": "Fulfilled"
                }

            },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': content
            }
        ]
    }


    return response

def greeting_intent(event, context):

    session = event['sessionState']
    content = "Hi there, how can I help?"

    response = {
        "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": "GreetingIntent",
                    "state": "Fulfilled"
                }

            },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': content
            }
        ]
    }

    return response



def lambda_handler(event, context):
    intent = event['sessionState']['intent']['name']

    if intent  == "GreetingIntent":
        return greeting_intent(event, context)

    elif intent  == "ThankYouIntent":
        return thankyou_intent(event, context)

    elif intent  == "DiningSuggestionsIntent":
        return dining_intent(event, context)

    return {}
