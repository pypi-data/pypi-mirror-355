import datetime
from google.cloud import storage
import os
from .constant import default_expiration_time, default_content_type
from typing import Generator

default_bucket_name = os.environ.get('BUCKET_NAME')

def gcp_upload(file_path, data, config):
    """
    Uploads a file to Google Cloud Storage.

    Args:
        file_path (str): The path or key under which the file will be stored.
        data (Buffer|Readable|string): The data or contents of the file to be uploaded.
            It can be provided as a Buffer, a Readable stream, or a string.
        config (dict): The configuration object.
            - bucketName (str): The name of the Google Cloud Storage bucket.
            - mimeType (str): The MIME type of the file.

    Returns:
        dict: An object representing the file path, if the upload is successful.

    Raises:
        Exception: If an error occurs during the upload process.
    """
    bucket_name = config.get('bucketName', default_bucket_name)
    mime_type = config.get('mimeType', default_content_type)

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.content_type = mime_type

    blob.upload_from_string(data)
    print('File uploaded successfully on gcp')
    return {
        'Key': file_path
    }


def gcp_download(file_path, config):
    """
    Downloads a file from Google Cloud Storage.

    Args:
        file_path (str): The path to the file to download.
        config (dict): The configuration object.
            - bucketName (str): The name of the Google Cloud Storage bucket.

    Returns:
        bytes: The downloaded file data.

    Raises:
        Exception: If an error occurs during the download process.
    """
    bucket_name = config.get('bucketName', default_bucket_name)

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    data = blob.download_as_bytes()

    return {
        'ContentType': blob.content_type,
        'Body': data
    }


def delete_gcs_object(config):
    """
    Deletes a GCS object.

    Args:
        config (dict): The configuration object.
            - filePath (str): The path to the file to delete.
            - bucketName (str): The name of the bucket to delete the file from. Defaults to "default_bucket_name".

    Raises:
        Exception: If an error occurs during the deletion process.
    """
    bucket_name = config.get('bucketName', default_bucket_name)
    file_path = config['filePath']

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.delete()

    print(f'File "{file_path}" deleted successfully.')

def get_gcs_presigned_url(config):
    """
    Gets a presigned URL for a GCS object.

    Args:
        config (dict): The configuration object.
            - filePath (str): The path to the file to get a presigned URL for.
            - expirationTime (int): The expiration time for the presigned URL in seconds. Defaults to default_expiration_time.
            - bucketName (str): The name of the bucket to get a presigned URL for. Defaults to "default_bucket_name".

    Returns:
        str: The presigned URL.

    Raises:
        Exception: If an error occurs during the generation of the presigned URL.
    """
    file_path = config['filePath']
    expiration_time = config.get('expirationTime', default_expiration_time)
    bucket_name = config.get('bucketName', default_bucket_name)

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(seconds=expiration_time),
        method="GET"
    )

    return url


def download_stream_gcp_file(
    file_path: str,
    config: dict,
    chunk_size: int = 1048576  # Default: 1MB chunks
) -> Generator[bytes, None, None]:
    """
    Streams a file from Google Cloud Storage in chunks.

    Args:
        file_path (str): The path to the file (blob) in the GCS bucket.
        config (dict): A configuration object containing:
            - 'bucketName' (str): The name of the GCS bucket.
        chunk_size (int): Size of each chunk in bytes (default: 1MB).

    Yields:
        Generator[bytes, None, None]: File content in chunks.

    Raises:
        ValueError: If 'bucketName' is missing from config.
        Exception: If an error occurs during the download.
    """
    try:
        # Extract required parameters
        bucket_name = config.get("bucketName", default_bucket_name)
        if not bucket_name:
            raise ValueError("The 'bucketName' parameter must be provided in config.")

        # Initialize GCP Storage Client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        # Open the blob as a stream
        with blob.open("rb") as file_stream:
            while chunk := file_stream.read(chunk_size):
                yield chunk

    except Exception as e:
        raise RuntimeError(f"Error streaming GCP file: {str(e)}")

def upload_stream_gcp_file(
    file_path: str,
    file_stream,
    config: dict
):
    """
    Streams an upload of a file to Google Cloud Storage in chunks.

    Args:
        file_path (str): The destination path of the file (blob) in the GCS bucket.
        file_stream (IO): A file-like object (e.g., open file in binary mode).
        config (dict): A configuration object containing:
            - 'bucketName' (str): The name of the GCS bucket.

    Raises:
        ValueError: If 'bucketName' is missing from config.
        Exception: If an error occurs during the upload.
    """
    try:
        # Extract required parameters
        bucket_name = config.get("bucketName", default_bucket_name)
        if not bucket_name:
            raise ValueError("The 'bucketName' parameter must be provided in config.")

        # Initialize GCP Storage Client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        # Upload in chunks
        blob.upload_from_file(file_stream, rewind=True)

    except Exception as e:
        raise RuntimeError(f"Error streaming upload to GCP: {str(e)}")

def upload_file_in_chunk_to_gcp_file(file_path, object_name, config):
    """
    Uploads a file to Google Cloud Storage. If the file is less than 5MB, it uploads directly.
    Otherwise, it uses resumable upload for larger files.
    
    Args:
        file_path (str): The local path of the file to be uploaded.
        object_name (str): The path or key under which the file will be stored in GCS.
        config (dict): The configuration object.
            - bucketName (str): The name of the Google Cloud Storage bucket.
            - mimeType (str): The MIME type of the file.
    
    Returns:
        dict: An object representing the file path, if the upload is successful.
        
    Raises:
        Exception: If an error occurs during the upload process.
    """
    try:
        bucket_name = config.get('bucketName', default_bucket_name)
        content_type = config.get('content_type', default_content_type)
        
        # Create GCS client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.content_type = content_type
        
        # Check file size
        file_size = os.path.getsize(file_path)
        
        # If file is less than 5MB, upload directly
        if file_size < 5 * 1024 * 1024:  # 5MB in bytes
            with open(file_path, "rb") as file_data:
                blob.upload_from_file(
                    file_data,
                    content_type=content_type
                )
            print(f"Successfully uploaded {object_name} to GCS bucket {bucket_name} (direct upload)")
        else:
            # For larger files, use chunked/resumable upload
            # The GCS client automatically handles chunking for large files when using resumable uploads
            with open(file_path, "rb") as file_data:
                blob.upload_from_file(
                    file_data,
                    content_type=content_type,
                    chunk_size=5 * 1024 * 1024,  # 5MB chunks
                    resumable=True
                )
            print(f"Successfully uploaded {object_name} to GCS bucket {bucket_name} (resumable upload)")
        
        return {"Key": object_name}
    
    except Exception as e:
        print(f"Failed to upload {object_name} to GCS: {e}")
        raise