import os
import datetime
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas, ContentSettings
from .constant import default_content_type, default_expiration_time
from typing import Generator
import base64

connection_string = os.environ.get('AZURE_BLOB_STORAGE_CONNECTION_STRING')
default_container_name = os.environ.get('BUCKET_NAME')

def azure_upload(file_path, data, config):
    """
    Uploads a file to Azure Blob Storage using the Azure Storage SDK.

    Args:
        file_path (str): The path or key under which the file will be stored.
        data (Buffer|Readable|string): The data or contents of the file to be uploaded.
            It can be provided as a Buffer, a Readable stream, or a string.
        config (dict): An optional configuration object.
            - bucketName (str): The name of the Azure Blob Storage container.
            - mimeType (str): The MIME type of the file being uploaded.

    Returns:
        dict: An object representing the file path, if the upload is successful.

    Raises:
        Exception: If an error occurs during the upload.
    """
    container_name = config.get('bucketName', default_container_name)
    mime_type = config.get('mimeType', default_content_type)

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    block_blob_client = container_client.get_blob_client(file_path)

    upload_options = {
        'blob_type': 'BlockBlob',
        'max_concurrency': 20
    }

    upload_options['content_settings'] = ContentSettings(content_type=mime_type)

    block_blob_client.upload_blob(data, **upload_options)
    print('File uploaded successfully on azure')
    return {
        'Key': file_path
    }


def azure_download(file_name, config):
    """
    Downloads a file from Azure Blob Storage using the Azure Storage SDK.

    Args:
        file_name (str): The name of the file to download.
        config (dict): An optional configuration object.
            - bucketName (str): The name of the Azure Blob Storage container.

    Returns:
        bytes: The file content as a byte string.

    Raises:
        Exception: If an error occurs during the download.
    """
    container_name = config.get('bucketName', default_container_name)

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    block_blob_client = container_client.get_blob_client(file_name)

    download_stream = block_blob_client.download_blob()
    content = download_stream.readall()
    properties = block_blob_client.get_blob_properties()
    content_settings = properties.get('content_settings', {})
    content_type = content_settings.get('content_type')
    return {
        'ContentType': content_type,
        'Body': content
    }


def delete_azure_blob(config):
    """
    Deletes an Azure blob.

    Args:
        config (dict): The configuration object.
            - bucketName (str): The name of the Azure blob container.
            - filePath (str): The name of the Azure blob file.

    Returns:
        None

    Raises:
        Exception: If an error occurs during the deletion.
    """
    container_name = config.get('bucketName', default_container_name)
    file_path = config['filePath']

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    block_blob_client = container_client.get_blob_client(file_path)

    block_blob_client.delete_blob()

    print(f'File "{file_path}" deleted successfully.')


def get_azure_blob_presigned_url(config):
    """
    Gets a presigned URL for an Azure blob.

    Args:
        config (dict): The configuration object.
            - filePath (str): The path to the file to get a presigned URL for.
            - expirationTime (int): The expiration time for the presigned URL in seconds. Defaults default_expiration_time.
            - bucketName (str): The name of the bucket to get a presigned URL for. Defaults to "default_bucket_name".

    Returns:
        str: The presigned URL.

    Raises:
        Exception: If an error occurs during the generation of the presigned URL.
    """
    container_name = config.get('bucketName', default_container_name)
    expiration_time = config.get('expirationTime',default_expiration_time)
    file_path = config['filePath']

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(file_path)

    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=container_name,
        blob_name=file_path,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration_time)
    )

    presigned_url = blob_client.url + '?' + sas_token

    return presigned_url


def download_stream_azure_file(
    file_name: str,
    config: dict,
    chunk_size: int = 1048576  # Default: 1MB chunks
) -> Generator[bytes, None, None]:
    """
    Streams a file from Azure Blob Storage in chunks.

    Args:
        file_name (str): The name of the file (blob) to download.
        config (dict): A configuration object containing:
            - 'bucketName' (str): The Azure Blob Storage container name.
            - 'connection_string' (str, optional): Azure connection string.
        chunk_size (int): Size of each chunk in bytes (default: 1MB).

    Yields:
        Generator[bytes, None, None]: File content in chunks.

    Raises:
        ValueError: If the bucket name or connection string is missing.
        Exception: If an error occurs during the download.
    """
    try:
        # Extract required parameters
        container_name = config.get("bucketName", default_container_name)

        # Initialize Azure Blob Service Client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        block_blob_client = container_client.get_blob_client(file_name)

        # Start downloading the blob as a stream
        download_stream = block_blob_client.download_blob()
        stream = download_stream

        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            yield chunk

    except Exception as e:
        raise RuntimeError(f"Error streaming Azure file: {str(e)}")


def upload_stream_azure_file(
    file_name: str,
    file_stream,
    config: dict
):
    """
    Streams an upload of a file to Azure Blob Storage in chunks.

    Args:
        file_name (str): The name of the file (blob) to upload.
        file_stream (IO): A file-like object (e.g., open file in binary mode).
        config (dict): A configuration object containing:
            - 'bucketName' (str): The Azure Blob Storage container name.
            - 'connection_string' (str, optional): Azure connection string.

    Raises:
        ValueError: If the bucket name or connection string is missing.
        Exception: If an error occurs during the upload.
    """
    try:
        # Extract required parameters
        container_name = config.get("bucketName", default_container_name)
        over_write_file = config.get("overwrite", True)

        # Initialize Azure Blob Service Client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(file_name)

        # Upload in chunks
        blob_client.upload_blob(file_stream, blob_type="BlockBlob", overwrite=over_write_file)

    except Exception as e:
        raise RuntimeError(f"Error streaming upload to Azure: {str(e)}")


def upload_file_in_chunk_to_azure_file(file_path, blob_path, config):
    """
    Uploads a file to Azure Blob Storage. If the file is less than 5MB, it uploads directly.
    Otherwise, it uses chunked upload.
    
    Args:
        file_path (str): The local path of the file to be uploaded.
        blob_path (str): The path or key under which the file will be stored in Azure.
        config (dict): Configuration object containing upload options.
            - bucketName (str): The name of the Azure Blob Storage container.
            - mimeType (str): The MIME type of the file being uploaded.
    
    Returns:
        dict: An object representing the file path, if the upload is successful.
        
    Raises:
        Exception: If an error occurs during the upload.
    """
    try:
        container_name = config.get('bucketName', default_container_name)
        content_type = config.get('content_type', default_content_type)
        
        # Create Azure clients
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        block_blob_client = container_client.get_blob_client(blob_path)
        
        # Check file size
        file_size = os.path.getsize(file_path)
        
        # Set content settings
        content_settings = ContentSettings(content_type=content_type)
        
        # If file is less than 5MB, upload directly
        if file_size < 5 * 1024 * 1024:  # 5MB in bytes
            with open(file_path, "rb") as data:
                block_blob_client.upload_blob(
                    data,
                    blob_type="BlockBlob",
                    content_settings=content_settings,
                    overwrite=True
                )
            print(f"Successfully uploaded {blob_path} to Azure container {container_name} (direct upload)")
        else:
            # For larger files, use chunked upload
            chunk_size = 4 * 1024 * 1024  # 4MB chunks
            block_list = []
            block_count = 0
            
            with open(file_path, "rb") as file_stream:
                while True:
                    read_data = file_stream.read(chunk_size)
                    if not read_data:
                        break
                    
                    # Generate unique block ID
                    block_id = f"{block_count:08d}"
                    encoded_block_id = base64.b64encode(block_id.encode()).decode()
                    
                    # Upload the block
                    block_blob_client.stage_block(
                        block_id=encoded_block_id,
                        data=read_data,
                        validate_content=True
                    )
                    
                    # Add the block ID to the block list
                    block_list.append(encoded_block_id)
                    block_count += 1
            
            # Commit the block list to create the blob
            block_blob_client.commit_block_list(
                block_list=block_list,
                content_settings=content_settings
            )
            
            print(f"Successfully uploaded {blob_path} to Azure container {container_name} (chunked upload)")
        
        return {"Key": blob_path}
    
    except Exception as e:
        print(f"Failed to upload {blob_path} to Azure: {e}")
        raise