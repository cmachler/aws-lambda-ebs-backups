# aws-lambda-ebs-backups
Python scripts to be run using AWS's Lambda service to Backup and Delete Snapshots of EBS Volumes

Read my blog post for more details on setting this up in Lambda if you have not used it before (http://www.evergreenitco.com/evergreenit-blog/2016/4/19/aws-ebs-backup-job-run-by-lambda).

## Setting Up IAM Permissions

First create an IAM policy called "ebs-backup-worker" with the following policy document:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "ec2:Describe*",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateSnapshot",
                "ec2:DeleteSnapshot",
                "ec2:CreateTags",
                "ec2:ModifySnapshotAttribute",
                "ec2:ResetSnapshotAttribute"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

Next create an IAM role also called "ebs-backup-worker" selete "AWS Lambda" as the Role type, then attach the "ebs-backup-worker" policy created above. When completed and you check the trust relationship in the role through "Edit Trust Relationship" it should look like below:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Create the Lambda Functions

Create two functions in Lambda using the Python 2.7 runtime, one for the backup script and one for the cleanup script. I recommend just using the 128 MB memory setting, and adjust the timeout to 10 seconds (longer in a larger environment). Set the event source to be "CloudWatch Events - Schedule" and set the Schedule expression to be a cron expression of your liking i.e. "cron(0 6 * * ? *)" if you want the job to be kicked off at 06:00 UTC, set the cleanup job to run a few minutes later.

Again if you need more details on setting this up please check my blog post (http://www.evergreenitco.com/evergreenit-blog/2016/4/19/aws-ebs-backup-job-run-by-lambda).
