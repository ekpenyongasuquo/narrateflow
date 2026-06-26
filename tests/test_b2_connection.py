import boto3
from app.core.config import settings

def test_b2_connection():
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.b2_endpoint}",
        aws_access_key_id=settings.b2_key_id,
        aws_secret_access_key=settings.b2_application_key,
    )
    response = s3.list_objects_v2(
        Bucket=settings.b2_bucket_name,
        MaxKeys=10
    )
    print(f"\n✅ Connected to bucket: {settings.b2_bucket_name}")
    print(f"✅ Objects found: {response.get('KeyCount', 0)}")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200