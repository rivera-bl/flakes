import boto3
from botocore.config import Config

my_config = Config(
    region_name = 'us-east-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

def main():
    ## list available services
	session = boto3.Session()
	services = session.get_available_services()
	print(services)

	# ec2 = boto3.resource('ec2', config=my_config)
