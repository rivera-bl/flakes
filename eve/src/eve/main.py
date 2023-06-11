import boto3
from datetime import datetime

# TODO add reload of events automatically every 3s
# # store the values in a cache to not loose it, overwrite every execution, cause range should be used if we need values from before a time, add default range for last 5minutes
# # should be a toggle
# TODO add argparse and create the function for the flags: --range, that takes 2 arguments that corresponds to the --start-time and --end-time options of lookup_events()

def print_columns(data):
    widths = [max(map(len, col)) for col in zip(*data)]
    for row in data:
        print("  ".join((val.ljust(width) for val, width in zip(row, widths))))

def get_cloudtrail_events():
    # Create a Boto3 CloudTrail client
    client = boto3.client('cloudtrail')
    
    # Define the desired fields to retrieve
    events = []
    header = ['EventTime', 'EventName', 'EventSource', 'Username', 'EventId']
    events.append(header)
    
    # Retrieve the CloudTrail events
    response = client.lookup_events()
    
    for event in response['Events']:
        event_data = [event['EventTime'].strftime('%H:%M:%S'), event['EventName'], event['EventSource']]
        if 'Username' in event:
            event_data.append(event['Username'])
        else:
            event_data.append('none')
        event_data.append(event['EventId'])
        events.append(event_data)

    return events

def main():
    events = get_cloudtrail_events()
    print_columns(events)
