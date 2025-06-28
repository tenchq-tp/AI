from pydantic_settings import BaseSettings
from urllib.parse import quote_plus
import boto3, os
import mimetypes
from botocore.client import Config
from botocore.exceptions import ClientError


class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int = 5432
    POSTGRES_HOST: str = "localhost"

    # S3 config
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str
    S3_ENDPOINT_URL: str 
    S3_REGION_NAME: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{quote_plus(self.POSTGRES_PASSWORD)}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

s3_client = boto3.client(
    "s3",
    endpoint_url="http://s3-bkk.nipa.cloud",
    aws_access_key_id="CIYNX4KY1YAW4FX0FVPE",
    aws_secret_access_key="ZMNjgYyIyE9Nu5qkMs3D0xHisvFNnqLR70lwbzRF",
    config=Config(signature_version='s3v4'),
    region_name="NCP-TH",
)

def upload_file_to_s3(file_data: bytes, s3_key: str, filename: str) -> bool:
    try:
        content_length = len(file_data)

        # ตรวจสอบ mime type จากชื่อไฟล์
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"

        print(f"📦 Uploading → {s3_key} ({content_length} bytes, type: {content_type})")

        s3_client.put_object(
            Bucket="asr",
            Key=s3_key,
            Body=file_data,
            ContentLength=content_length,
            ContentType=content_type
        )

        print(f"✅ Upload success: {s3_key}")
        return True

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def delete_s3_folder(s3_prefix: str):
    try:
        response = s3_client.list_objects_v2(Bucket="asr", Prefix=s3_prefix)
        if "Contents" in response:
            for obj in response["Contents"]:
                s3_client.delete_object(Bucket="asr", Key=obj["Key"])
                print(f"🗑️ Deleted from S3: {obj['Key']}")
        else:
            print("ℹ️ No files found to delete in S3.")
    except ClientError as e:
        print(f"❌ Failed to delete from S3: {e}")
    
def generate_presigned_url(s3_key: str, expires_in: int = 36000) -> str:
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": "asr", "Key": s3_key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        print(f"❌ Failed to generate presigned URL: {e}")
        return ""
 
 