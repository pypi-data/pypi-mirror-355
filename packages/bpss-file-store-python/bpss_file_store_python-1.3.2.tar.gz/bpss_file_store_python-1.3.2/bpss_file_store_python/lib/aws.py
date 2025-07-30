import boto3
import os
from .constant  import default_content_type, default_expiration_time
from typing import Generator
from botocore.exceptions import NoCredentialsError
from io import BytesIO


default_bucket_name = os.getenv('BUCKET_NAME')
region_name = os.getenv('AWS_REGION')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

aws_config = {
    'region_name': region_name,
    'aws_access_key_id': aws_access_key_id,
    'aws_secret_access_key': aws_secret_access_key
}

def aws_upload(file_path, data, config={}):
    """
    Uploads a file to Amazon S3 using the AWS SDK.

    Args:
        file_path (str): The path or key under which the file will be stored in the S3 bucket.
        data (Buffer|Readable|string): The data or contents of the file to be uploaded.
            It can be provided as a Buffer, a Readable stream, or a string.
        config (dict, optional): An optional configuration object.
            - bucketName (str): The name of the S3 bucket where the file will be uploaded.
            - mimeType (str): The MIME type or content type of the file being uploaded.

    Returns:
        dict: An object representing the file path, if the upload is successful.

    Raises:
        Exception: If the upload fails, an exception will be raised.
    """
    bucket_name = config.get('bucketName', default_bucket_name)
    mime_type = config.get('mimeType', default_content_type)
    s3 = boto3.client('s3', **aws_config)
    params = {
        'Bucket': bucket_name,
        'Key': file_path,
        'Fileobj': data
    }

    params['ExtraArgs'] = { 'ContentType': mime_type}
    
    s3.upload_fileobj(**params)
    print('File uploaded successfully on aws')
    return {
        'Key': file_path
    }

def aws_download(file_path, config={}):
    """
    Downloads an object from Amazon S3 using the AWS SDK.

    Args:
        file_path (str): The path or key of the object to be downloaded from the S3 bucket.
        config (dict, optional): An optional configuration object.
            - bucketName (str): The name of the S3 bucket from which the object will be downloaded.

    Returns:
        bytes: The downloaded object data.

    Raises:
        Exception: If the download fails, an exception will be raised.
    """
    bucket_name = config.get('bucketName', default_bucket_name)

    s3 = boto3.client('s3', **aws_config)
    params = {
        'Bucket': bucket_name,
        'Key': file_path
    }

    response = s3.get_object(**params)
    return {
        'ContentType': response.get('ContentType'),
        'Body': response['Body'].read()
    }

def delete_s3_object(config={}):
    """
    Deletes an object from Amazon S3 using the AWS SDK.

    Args:
        file_path (str): The path or key of the object to be deleted from the S3 bucket.
        config (dict, optional): An optional configuration object.
            - bucketName (str): The name of the S3 bucket from which the object will be deleted.

    Returns:
        None

    Raises:
        Exception: If the deletion fails, an exception will be raised.
    """
    bucket_name = config.get('bucketName', default_bucket_name)
    file_path = config['filePath']

    s3 = boto3.client('s3', **aws_config)
    params = {
        'Bucket': bucket_name,
        'Key': file_path
    }
    s3.delete_object(**params)

    print(f'File "{file_path}" deleted successfully.')

def get_s3_presigned_url(config={}):
    """
    Generates a presigned URL for downloading an object from Amazon S3 using the AWS SDK.

    Args:
        config (dict): The configuration object.
            - filePath (str): The path to the file to get a presigned URL for.
            - expirationTime (int): The expiration time for the presigned URL in seconds. Defaults to default_expiration_time.
            - bucketName (str): The name of the bucket to get a presigned URL for. Defaults to "default_bucket_name".

    Returns:
        str: The presigned URL.

    Raises:
        Exception: If an error occurs, an exception will be raised.
    """
    bucket_name = config.get('bucketName', default_bucket_name)
    file_path = config['filePath']
    expiration_time = config.get('expirationTime', default_expiration_time)

    s3 = boto3.client('s3', **aws_config)
    params = {
        'Bucket': bucket_name,
        'Key': file_path
    }

    url = s3.generate_presigned_url('get_object', Params=params, ExpiresIn = expiration_time)
    return url



def download_stream_s3_file(
    key: str,
    chunk_size: int = 1048576,  # Default: 1MB chunks
    config={}
) -> Generator[bytes, None, None]:
    """
    Streams a file from Amazon S3 in chunks.

    Args:
        key (str): The S3 object key (file path).
        chunk_size (int): Size of each chunk in bytes (default: 1MB).
        config (Optional[dict]): AWS credentials/configuration (e.g., `{"aws_access_key_id": "...", "aws_secret_access_key": "..."}`).
    Yields:
        Generator[bytes, None, None]: File content in chunks.

    Raises:
        RuntimeError: If AWS credentials are missing.
        Exception: For other S3 errors.
    """
    try:        
        # Create S3 client
        s3_client = boto3.client('s3', **aws_config)

        bucket_name = config.get('bucketName', default_bucket_name)

        # Get the file stream
        file_stream = s3_client.get_object(Bucket=bucket_name, Key=key)["Body"]
        
        # Stream the file in chunks
        for chunk in file_stream.iter_chunks(chunk_size=chunk_size):
            yield chunk

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found. Please configure them.")
    except Exception as e:
        raise RuntimeError(f"Error streaming S3 file: {str(e)}")



def upload_stream_to_s3(file_stream: BytesIO, key: str, config: dict):
    """
    Uploads a file stream to Amazon S3.

    Args:
        file_stream (BytesIO): The file stream to upload.
        key (str): The S3 object key (file path).
        config (dict): bucketName name

    Raises:
        RuntimeError: If AWS credentials are missing.
        Exception: For other S3 errors.
    """
    try:
        # Create S3 client
        s3_client = boto3.client('s3', **aws_config)
        bucket_name = config.get('bucketName', default_bucket_name)

        if not bucket_name:
            raise ValueError("Bucket name is required in the config.")
        
        # Reset stream to the beginning before uploading
        file_stream.seek(0)

        # Upload stream to S3
        s3_client.upload_fileobj(file_stream, bucket_name, key)
        print(f"File uploaded successfully to {bucket_name}/{key}")

    except boto3.exceptions.NoCredentialsError:
        raise RuntimeError("AWS credentials not found. Please configure them.")
    except Exception as e:
        raise RuntimeError(f"Error uploading stream to S3: {str(e)}")


def upload_file_in_chunk_to_s3(file_path: str, s3_key: str, config: dict):
    """
    Uploads a file to AWS S3. If the file is less than 5MB, it uploads directly.
    Otherwise, it uses Multipart Upload.
    
    Args:
        file_path: Local file path
        s3_key: The file key (path) in S3
        config: Dictionary containing AWS configuration
    """
    try:
        # Create S3 client
        s3_client = boto3.client('s3', **aws_config)
        bucket_name = config.get('bucketName', default_bucket_name)
        content_type = config.get('content_type', default_content_type)
        
        # Check file size
        file_size = os.path.getsize(file_path)
        
        # If file is less than 5MB, upload directly
        if file_size < 5 * 1024 * 1024:  # 5MB in bytes
            with open(file_path, "rb") as file_data:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=file_data,
                    ContentType=content_type
                )
            print(f"Successfully uploaded {s3_key} to S3 bucket {bucket_name} (direct upload)")
        else:
            # For larger files, use multipart upload
            # Start a multipart upload
            response = s3_client.create_multipart_upload(Bucket=bucket_name, Key=s3_key, ContentType=content_type)
            upload_id = response["UploadId"]
            parts = []
            part_number = 1
            chunk_size = 5 * 1024 * 1024  # 5MB chunks (S3 requires at least 5MB for multipart)
            
            with open(file_path, "rb") as file_stream:
                while chunk := file_stream.read(chunk_size):
                    part_response = s3_client.upload_part(
                        Bucket=bucket_name,
                        Key=s3_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=chunk
                    )
                    parts.append({"PartNumber": part_number, "ETag": part_response["ETag"]})
                    part_number += 1
            
            # Complete the multipart upload
            s3_client.complete_multipart_upload(
                Bucket=bucket_name,
                Key=s3_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts}
            )
            print(f"Successfully uploaded {s3_key} to S3 bucket {bucket_name} (multipart upload)")
    
    except NoCredentialsError:
        print("AWS credentials not found! Check your AWS_ACCESS_KEY and AWS_SECRET_KEY.")
    except Exception as e:
        print(f"Failed to upload {s3_key} to S3: {e}")
