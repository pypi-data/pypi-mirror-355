from setuptools import setup, find_packages

# Read the README.md file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='bpss_file_store_python',
    version='1.3.2',
    packages=find_packages(),
    install_requires=[
        'boto3==1.26.150',
        'azure-storage-blob==12.16.0',
        'google-cloud-storage==2.9.0'
    ],
    long_description=long_description,
    long_description_content_type="text/markdown", 
    # Other metadata and configuration
)
