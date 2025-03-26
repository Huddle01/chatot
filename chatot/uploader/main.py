import boto3
import os
from botocore.exceptions import ClientError
import logging
from dotenv import load_dotenv

load_dotenv()

account_id = os.getenv("ACCOUNT_ID")
access_key_id = os.getenv("ACCESS_KEY_ID")
access_key_secret = os.getenv("ACCESS_KEY_SECRET")
bucket_name = os.getenv("BUCKET_NAME")
domain = os.getenv("CUSTOM_DOMAIN")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_s3_client():
    if (
        account_id is None
        or access_key_id is None
        or access_key_secret is None
        or bucket_name is None
    ):
        logger.error(f"Env values: account id: {account_id}, key_id: {access_key_id}, key_secret: {access_key_secret}, bucket: {bucket_name}")
        raise Exception(
            "Account ID, Access Key Id, Access Key Secret or Bucket Name is not present"
        )

    r2 = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=access_key_secret,
        region_name="auto"
    )

    return r2


def upload_file(file_name: str, object_name=None):
    if object_name is None:
        object_name = file_name

    r2 = get_s3_client()

    upload_try = 0

    while upload_try < 3:
        try:
            r2.upload_file(file_name, bucket_name, object_name)
            uploaded_file_url = f"https://{domain}/{object_name}" if domain else f"https://{account_id}.r2.cloudflarestorage.com/{bucket_name}/{object_name}"
            return uploaded_file_url
        except ClientError as e:
            logger.error(f"Error occurred while uploading file: {e}")
        finally:
            upload_try = upload_try + 1

    raise Exception("Unable to upload file")
