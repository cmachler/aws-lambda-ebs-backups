import boto3
import collections
import datetime

regions = ['us-west-2','us-east-2']

def lambda_handler(event, context):
    for region in regions:
        ec = boto3.client('ec2', region_name=region)
        reservations = ec.describe_instances(
            Filters=[
                {'Name': 'tag-key', 'Values': ['backup', 'Backup']},
            ]
        ).get(
            'Reservations', []
        )

        instances = sum(
            [
                [i for i in r['Instances']]
                for r in reservations
            ], [])

        print "Found %d instances that need backing up" % len(instances)

        to_tag_retention = collections.defaultdict(list)
        to_tag_mount_point = collections.defaultdict(list)

        for instance in instances:
            try:
                retention_days = [
                    int(t.get('Value')) for t in instance['Tags']
                    if t['Key'] == 'Retention'][0]
            except IndexError:
                retention_days = 7

            for dev in instance['BlockDeviceMappings']:
                if dev.get('Ebs', None) is None:
                    continue
                vol_id = dev['Ebs']['VolumeId']
                dev_attachment = dev['DeviceName']
                print "Found EBS volume %s on instance %s attached to %s" % (
                    vol_id, instance['InstanceId'], dev_attachment)

                snap = ec.create_snapshot(
                    VolumeId=vol_id,
                    Description=instance['InstanceId'],
                )

                to_tag_retention[retention_days].append(snap['SnapshotId'])
                to_tag_mount_point[vol_id].append(snap['SnapshotId'])


                print "Retaining snapshot %s of volume %s from instance %s for %d days" % (
                    snap['SnapshotId'],
                    vol_id,
                    instance['InstanceId'],
                    retention_days,
                )

                ec.create_tags(
                    Resources=to_tag_mount_point[vol_id],
                    Tags=[
                        {'Key': 'Name', 'Value': dev_attachment},
                    ]
                )

        for retention_days in to_tag_retention.keys():
            delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
            delete_fmt = delete_date.strftime('%Y-%m-%d')
            print "Will delete %d snapshots on %s" % (len(to_tag_retention[retention_days]), delete_fmt)
            ec.create_tags(
                Resources=to_tag_retention[retention_days],
                Tags=[
                    {'Key': 'DeleteOn', 'Value': delete_fmt},
                ]
            )
