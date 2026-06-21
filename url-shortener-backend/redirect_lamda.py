import json
import boto3
import redis
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('url-shortener-table')

REDIS_HOST = os.environ.get('REDIS_HOST')
redis_client = redis.Redis(
    host=REDIS_HOST, 
    port=6379, 
    decode_responses=True, 
    socket_timeout=2,
    ssl=True
)

def lambda_handler(event, context):
    short_id = event.get('pathParameters', {}).get('proxy')
    if not short_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing short link identifier'})}

    try:
        cached_url = redis_client.get(short_id)
        if cached_url:
            return {
                'statusCode': 302,
                'headers': { 'Location': cached_url },
                'body': json.dumps({'message': 'Redirecting via Cache...'})
            }
    except redis.exceptions.ConnectionError as e:
        print(f"⚠️ Redis Connection Error: {str(e)}")

    response = table.get_item(Key={'short_id': short_id})
    item = response.get('Item')
    if not item:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Short URL not found'})}
        
    long_url = item['long_url']
    
    try:
        redis_client.setex(name=short_id, time=86400, value=long_url)
    except Exception as e:
        print(f"⚠️ Failed to write to Redis: {str(e)}")

    return {
        'statusCode': 302,
        'headers': { 'Location': long_url },
        'body': json.dumps({'message': 'Redirecting via Database...'})
    }