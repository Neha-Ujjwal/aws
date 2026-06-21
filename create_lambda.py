import json
import boto3
import random
import string
import redis

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('url-shortener-table')

# NOTE: Endpoints are passed via environment variables for clean configuration management
import os
REDIS_HOST = os.environ.get('REDIS_HOST')

redis_client = redis.Redis(
    host=REDIS_HOST, 
    port=6379, 
    decode_responses=True, 
    socket_timeout=2,
    ssl=True
)

def generate_short_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
    except Exception:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON request'})}
        
    long_url = body.get('long_url')
    if not long_url:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing long_url'})}

    short_id = generate_short_id()

    table.put_item(Item={'short_id': short_id, 'long_url': long_url})
    
    try:
        redis_client.setex(name=short_id, time=86400, value=long_url)
    except Exception as e:
        print(f"⚠️ Cache seeding bypassed: {str(e)}")

    return {
        'statusCode': 201,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'short_id': short_id,
            'long_url': long_url
        })
    }