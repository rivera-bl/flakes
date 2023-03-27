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
	ec2 = boto3.resource('ec2', config=my_config)
	for instance in ec2.instances.all():
		print(instance.id)
