### Install this package
Add the below contents to `~/.pip/pip.conf` file to authenticate the private repository
```
[global]
extra-index-url = http://username:password@nexus-repo.betterplace.co.in:8081/repository/pypi-hosted/simple
trusted-host = nexus-repo.betterplace.co.in
```

To Install
```
pip3 install bpss-file-store-python==1.0.0
```

### Publish the package
1. python setup.py sdist bdist_wheel
2. pip install twine
3. twine upload --repository-url http://nexus-repo.betterplace.co.in:8081/repository/pypi-hosted/ dist/*  

#### Required Environment Variables for Azure
```
CLOUD_PROVIDER=azure
BUCKET_NAME
AZURE_BLOB_STORAGE_CONNECTION_STRING
```

#### Required Environment Variables for AWS
```
CLOUD_PROVIDER=aws
BUCKET_NAME
AWS_REGION
AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY
```

#### Required Environment Variables for GCP
```
CLOUD_PROVIDER=gcp
BUCKET_NAME
GCP_PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS
```

## Example of using in a python project which uses Docker

`Dockerfile`
```
# Specify the base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# These two commands copy the pip.conf from the secrets and copy it to ~/.pip.conf
RUN mkdir ~/.pip
RUN --mount=type=secret,id=pip.conf \
   cp /run/secrets/pip.conf ~/.pip/pip.conf

# Copy the requirements file
COPY requirements.txt .

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Expose the port on which the app will run
EXPOSE 5000

# Set the entrypoint command to run the app
CMD ["python", "app.py"]
```

##### Docker build command (assuming that pip.conf is in /Users/frank/.pip/pip.conf)
```
docker build --secret id=pip.conf,src=/Users/frank/.pip/pip.conf -t betterplace/test-file-store-pytion .
```

##### Example Implementation
```
from bpss_file_store_python.file_store import upload_file, delete_file, download_file, get_presigned_download_url, stream_file

source_file_path = "<file path present on local which need to upload on cloud>"
destination_file_path = "<file path name to upload on cloud>"

// upload
file_as_binary = open(source_file_path, "rb").read()
file_as_binary = io.BytesIO(file_as_binary)
mime_type = mime.from_file(source_file_path)
upload_file(destination_file_path, file_as_binary, {
    'mimeType': mime_type
})

// download
response = download_file(source_file_path)
file_data = response['Body']
with open(destination_file_path, 'wb') as file:
   file.write(file_data)

// delete
delete_file({'filePath' : source_file_path})

// get presigned_url
url = get_presigned_download_url({'filePath' : source_file_path})   

// download stream_file 
for chunk in stream_file(file_key, bucket_name=bucket, chunk_size=2 * 1024 * 1024):
    process_chunk(chunk)  # Replace with your processing logic

// upload stream file
file_stream = BytesIO(b"Hello, this is a test upload!")
upload_stream_file(file_stream, {"filePath": "test_folder/test_file.txt"})

// upload file in chunk 
local_file_path = '/path/to/your/file.pdf'
file_key = 'uploads/file.pdf'
upload_file_in_chunk(local_file_path, file_key, config)
```