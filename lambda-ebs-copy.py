import boto3
import re
import datetime
import base64
import os
import json

COPY_LIMIT = 5
RETENTION_DAYS = 7
CROSS_COPIED_TAG = 'CrossCopied'
base64_region = os.environ['aws_regions']
copy_region = os.environ['aws_copy_region']
iam = boto3.client('iam')
aws_sns_arn = os.getenv('aws_sns_arn', None)


def snapshot_is_copied(snap):
    for kv in snap['Tags']:
        if 'Key' in kv and kv['Key'] == CROSS_COPIED_TAG:
            return True
    return False


def send_to_sns(subject, message):
    if aws_sns_arn is None:
        return

    print "Sending notification to: %s" % aws_sns_arn

    client = boto3.client('sns')

    response = client.publish(
        TargetArn=aws_sns_arn,
        Message=message,
        Subject=subject)

    if 'MessageId' in response:
        print "Notification sent with message id: %s" % response['MessageId']
    else:
        print "Sending notification failed with response: %s" % str(response)


def lambda_handler(event, context):
    """
    This function copies snapshots to a different region
    for increased redundancy.
    """
    decoded_regions = base64.b64decode(base64_region)
    regions = decoded_regions.split(',')

    print "Copying snapshots in region: %s" % copy_region

    dest_conn = boto3.client('ec2', region_name=copy_region)
    # There is a COPY_LIMIT concurrent copy operations limit
    copy_limit_counter = 0
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
            account_ids.append(
                re.search(r'(arn:aws:sts::)([0-9]+)', str(e)).groups()[1])

        delete_on = datetime.date.today() + datetime.timedelta(days=RETENTION_DAYS)
        filters = [
            {'Name': 'tag-key', 'Values': ['DeleteOn']},
            {'Name': 'tag-value', 'Values': [delete_on.strftime('%Y-%m-%d')]},
        ]
        snapshot_response = ec.describe_snapshots(
            OwnerIds=account_ids, Filters=filters)

        print "Analyzing %d snapshots for copying in region %s" % (
            len(snapshot_response['Snapshots']),
            region)

        for snap in snapshot_response['Snapshots']:
            if copy_limit_counter == COPY_LIMIT:
                return "{} copies limit reached".format(COPY_LIMIT)
            if snapshot_is_copied(snap):
                continue
            print "Copying snapshot %s" % snap['SnapshotId']
            copied_snap = dest_conn.copy_snapshot(SourceRegion=region, SourceSnapshotId=snap['SnapshotId'],
                                                  Description='Cross copied from {} for {}'.format(
                                                      region, snap['Description'])
                                                  )
            dest_conn.create_tags(
                Resources=[copied_snap['SnapshotId']],
                Tags=[
                    {
                        'Key': 'DeleteOn',
                        'Value': [x['Value'] for x in snap['Tags'] if x['Key'] == 'DeleteOn'][0],
                    },
                ],
            )
            ec.create_tags(
                Resources=[snap['SnapshotId']],
                Tags=[
                    {
                        'Key': CROSS_COPIED_TAG,
                        'Value': copy_region,
                    },
                ],
            )
            copy_limit_counter += 1

        message = "started copying {} snapshots in region {}".format(
            len(snapshot_response['Snapshots']), region)
        send_to_sns('EBS Copying Done', message)
