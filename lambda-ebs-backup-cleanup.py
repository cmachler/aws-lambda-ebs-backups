import boto3
import re
import datetime
import base64
import os

base64_region = os.environ['aws_regions']

iam = boto3.client('iam')

"""
This function looks at *all* snapshots that have a "DeleteOn" tag containing
the current day formatted as YYYY-MM-DD. This function should be run at least
daily.
"""

def lambda_handler(event, context):
    decoded_regions = base64.b64decode(base64_region)
    regions = decoded_regions.split(',')

    print "Cleaning up snapshots in regions: %s" % regions

    for region in regions:
        ec = boto3.client('ec2', region_name=region)
        account_ids = list()
        try:
            """
            You can replace this try/except by filling in `account_ids` yourself.
            Get your account ID with:
            > import boto3
            > iam = boto3.client('iam')
            > print iam.get_user()['User']['Arn'].split(':')[4]
            """
            iam.get_user()
        except Exception as e:
            # use the exception message to get the account ID the function executes under
            account_ids.append(re.search(r'(arn:aws:sts::)([0-9]+)', str(e)).groups()[1])


        delete_on = datetime.date.today().strftime('%Y-%m-%d')
        filters = [
            {'Name': 'tag-key', 'Values': ['DeleteOn']},
            {'Name': 'tag-value', 'Values': [delete_on]},
        ]
        snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters)

        print "Found %d snapshots that need deleting in region %s on %s" % (
            len(snapshot_response['Snapshots']),
            region,
            delete_on)

        for snap in snapshot_response['Snapshots']:
            print "Deleting snapshot %s" % snap['SnapshotId']
            ec.delete_snapshot(SnapshotId=snap['SnapshotId'])
