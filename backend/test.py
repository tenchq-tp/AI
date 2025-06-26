import mimetypes
import boto3
from botocore.config import Config
import os
import io

import urllib3
#urllib3.disable_warnings()
s3_client = boto3.client(
    "s3",
    endpoint_url="https://s3-bkk.nipa.cloud",
    aws_access_key_id="CIYNX4KY1YAW4FX0FVPE",
    aws_secret_access_key="ZMNjgYyIyE9Nu5qkMs3D0xHisvFNnqLR70lwbzRF",
    config=Config(signature_version='s3v4'),
    region_name="NCP-TH",
    verify=False
)

#s3_key = '/asr/02976IMK089CJE3JKI21DB5AES02O0IR_2024-03-01_13-33-53_0.mp3'
# file_path = 'D:/Internship/AI/Hotel/02976IMK089CJE3JKI21DB5AES02O0IP/02976IMK089CJE3JKI21DB5AES02O0IP.mp3'
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

        # s3_client.upload_file(
        #     Filename=file_path,
        #     Bucket="asr",
        #     Key=s3_key,
        #     ExtraArgs={"ContentType": content_type}
        # )
        
        # s3_client.put_object(
        #     Bucket="asr",
        #     Key=s3_key,
        #     Body=io.BytesIO(data),
        #     ContentLength=len(data),
        #     ContentType=content_type
        # )
        # print(s3_client)
        # s3_client.put_object(
        #     Bucket="asr",
        #     Key=s3_key.lstrip("/"),
        #     Body=io.BytesIO(data),  # Ensure stream-like object
        #     ContentLength=content_length,
        #     ContentType=content_type
        # ) 
        
        # s3_client.put_object(
        #     Bucket="asr",
        #     Key=s3_key.lstrip("/"),
        #     Body=data,
        #     ContentType=content_type
        # )
        
        s3_client.upload_file(
            Filename=file_path,
            Bucket="asr",
            Key=s3_key.lstrip("/"),
            ExtraArgs={"ContentType": content_type}
        )
        
        
        s3_client.up
            
        print(f"✅ Upload success: {s3_key}")
        return True

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False
    
upload_file_to_s3('D:\\Internship\\AI\\Hotel\\02976IMK089CJE3JKI21DB5AES02O0IP\\02976IMK089CJE3JKI21DB5AES02O0IP_2024-03-01_13-32-27_0.mp3', '02976IMK089CJE3JKI21DB5AES02O0IR_2024-03-01_13-33-53_0.mp3')