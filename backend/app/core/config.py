from pydantic_settings import BaseSettings
from urllib.parse import quote_plus
import boto3, os
import mimetypes
from botocore.client import Config
from io import BytesIO


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

def upload_file_to_s3(file_path: str, s3_key: str) -> bool:
    try:
        if not os.path.isfile(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        with open(file_path, "rb") as f:
            data = f.read()
        content_length = len(data)

        # 👇 ตรวจสอบ mime type จากนามสกุลไฟล์
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"  # fallback

        print(f"📦 Uploading {file_path} → {s3_key} ({content_length} bytes, type: {content_type})")

        s3_client.put_object(
            Bucket="asr",
            Key=s3_key,
            Body=data,
            ContentLength=content_length,
            ContentType=content_type
        )

        print(f"✅ Upload success: {s3_key}")
        return True

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False


    
    