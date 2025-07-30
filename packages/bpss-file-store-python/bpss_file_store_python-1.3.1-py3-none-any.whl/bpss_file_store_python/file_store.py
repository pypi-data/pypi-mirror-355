import os
from .lib.aws import aws_download, aws_upload, delete_s3_object, get_s3_presigned_url, download_stream_s3_file, upload_stream_to_s3, upload_file_in_chunk_to_s3
from .lib.gcp import gcp_download, gcp_upload, delete_gcs_object, get_gcs_presigned_url, download_stream_gcp_file, upload_stream_gcp_file, upload_file_in_chunk_to_gcp_file
from .lib.azure import azure_download, azure_upload, delete_azure_blob, get_azure_blob_presigned_url, download_stream_azure_file, upload_stream_azure_file, upload_file_in_chunk_to_azure_file
from typing import Generator
from io import BytesIO

cloudProvider = os.environ.get('CLOUD_PROVIDER')


def upload_file(file_path, data, config=None):
    """
    Uploads a file to a cloud storage provider.

    Args:
        file_path (str): The path to the file to upload.
        data (str): The data to upload.
        config (dict): The configuration object (optional).

    Returns:
        The upload result.

    Raises:
        ValueError: If an invalid cloud provider is specified.
    """
    if config is None:
        config = {}
    if cloudProvider.lower() == "aws":
        return aws_upload(file_path, data, config)
    elif cloudProvider.lower() == "gcp":
        return gcp_upload(file_path, data, config)
    elif cloudProvider.lower() == "azure":
        return azure_upload(file_path, data, config)
    else:
        raise ValueError("Invalid cloud provider specified.")


def download_file(file_path, config=None):
    """
    Downloads a file from a cloud provider.

    Args:
        file_path (str): The path to the file to download.
        config (dict): The configuration object (optional).

    Returns:
        The downloaded file.

    Raises:
        ValueError: If an invalid cloud provider is specified.
    """
    if config is None:
        config = {}
    if cloudProvider.lower() == "aws":
        return aws_download(file_path, config)
    elif cloudProvider.lower() == "gcp":
        return gcp_download(file_path, config)
    elif cloudProvider.lower() == "azure":
        return azure_download(file_path, config)
    else:
        raise ValueError("Invalid cloud provider specified.")


def delete_file(config=None):
    """
    Deletes a file from a cloud provider.

    Args:
        config (dict): The configuration object (optional).

    Returns:
        None

    Raises:
        ValueError: If an invalid cloud provider is specified.
    """
    if cloudProvider.lower() == "aws":
        return delete_s3_object(config)
    elif cloudProvider.lower() == "gcp":
        return delete_gcs_object(config)
    elif cloudProvider.lower() == "azure":
        return delete_azure_blob(config)
    else:
        raise ValueError("Invalid cloud provider specified.")


def get_presigned_download_url(config=None):
    """
    Generate a presigned download URL based on the cloud provider specified in the environment variable.

    Args:
        config (dict): An object containing the filePath and expiryTime.
            filePath (str): The path of the file to generate a presigned download URL for.
            expirationTime (int): The expiration time of the presigned URL in seconds. Defaults to 3600 seconds.

    Returns:
        The presigned download URL.

    Raises:
        ValueError: If an invalid cloud provider is specified.
    """
    if cloudProvider.lower() == "aws":
        return get_s3_presigned_url(config)
    elif cloudProvider.lower() == "gcp":
        return get_gcs_presigned_url(config)
    elif cloudProvider.lower() == "azure":
        return get_azure_blob_presigned_url(config)
    else:
        raise ValueError("Invalid cloud provider specified.")
    

def download_stream_file(config: dict, chunk_size: int = 1048576) -> Generator[bytes, None, None]:
    """
    Streams a file from the appropriate cloud provider (AWS, GCP, or Azure) in chunks.

    Args:
        config (dict): A configuration object containing:
            - 'filePath' (str): The path to the file.
            - 'bucketName' (str): The bucket/container name.
            - Additional required parameters for the respective cloud provider.
        chunk_size (int): Size of each chunk in bytes (default: 1MB).

    Yields:
        Generator[bytes, None, None]: File content in chunks.

    Raises:
        ValueError: If an invalid cloud provider is specified.
    """
    cloud_provider = cloudProvider.lower()
    if cloud_provider == "aws":
        yield from  download_stream_s3_file(config["filePath"], chunk_size=chunk_size, config=config)
    elif cloud_provider == "gcp":
        yield from download_stream_gcp_file(config["filePath"], config, chunk_size=chunk_size)
    elif cloud_provider == "azure":
        yield from download_stream_azure_file(config["filePath"], config, chunk_size=chunk_size)
    else:
        raise ValueError("Invalid cloud provider specified.")


def upload_stream_file(file_stream: BytesIO, config: dict) -> Generator[bytes, None, None]:
    """
    Streams a file upload to the appropriate cloud provider (AWS, GCP, or Azure).

    Args:
        file_stream (BytesIO): The file stream to upload.
        config (dict): A configuration object containing:
            - 'filePath' (str): The destination path of the file.
            - 'bucketName' (str): The bucket/container name.
            - 'cloudProvider' (str): The cloud provider ('aws', 'gcp', 'azure').
            - Additional required parameters for the respective cloud provider.
    Raises:
        ValueError: If an invalid cloud provider is specified.
    """
    cloud_provider = cloudProvider.lower()
    if cloud_provider == "aws":
        upload_stream_to_s3(file_stream, config["filePath"], config)
    elif cloud_provider == "gcp":
        upload_stream_gcp_file(config["filePath"], file_stream, config)
    elif cloud_provider == "azure":
        upload_stream_azure_file(config["filePath"], file_stream, config)
    else:
        raise ValueError("Invalid cloud provider specified.")


def upload_file_in_chunk(file_path, key, config=None):

    """
    Uploads a file to a cloud storage provider (AWS, GCP, or Azure) in chunks.

    Args:
        file_path (str): The local file path of the file to upload.
        key (str): The destination key/path where the file should be stored in the cloud.
        config (dict, optional): Configuration settings for the upload process.
    Returns:
        dict: The upload result.

    Raises:
        ValueError: If an invalid cloud provider is specified.
    """

    cloud_provider = cloudProvider.lower()
    if config is None:
        config = {}
    if cloud_provider == "aws":
        return upload_file_in_chunk_to_s3(file_path, key, config)
    elif cloud_provider == "gcp":
        return upload_file_in_chunk_to_gcp_file(file_path, key, config)
    elif cloud_provider == "azure":
        return upload_file_in_chunk_to_azure_file(file_path, key, config)
    else:
        raise ValueError("Invalid cloud provider specified.")