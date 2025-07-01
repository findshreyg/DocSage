import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client("s3")

dynamodb = boto3.resource("dynamodb")
metadata_table = dynamodb.Table("IDPMetadata")

def generate_presigned_url(user_id: str, file_hash: str, expires_in: int = 3600):
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME is not set. Check your .env or environment variables.")

    # Look up S3 key from DynamoDB
    try:
        result = metadata_table.get_item(Key={"user_id": user_id, "hash": file_hash})
    except ClientError as e:
        raise Exception(f"DynamoDB error when fetching metadata: {e}")

    if "Item" not in result:
        raise Exception("File metadata not found for this hash and user.")

    s3_key = result["Item"].get("s3_key")
    if not s3_key:
        raise Exception("S3 key is missing in metadata record.")

    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        raise Exception(f"Could not generate presigned URL due to AWS error: {e}")
    except Exception as e:
        raise Exception(f"Could not generate presigned URL: {str(e)}")