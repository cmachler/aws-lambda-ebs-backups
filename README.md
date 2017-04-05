# aws-lambda-ebs-backups
Python scripts to be run using AWS's Lambda service to Create and Delete Snapshots of EBS Volumes

[Read my blog post for more details on setting this up in Lambda if you have not used it before.] (http://www.evergreenitco.com/evergreenit-blog/2016/4/19/aws-ebs-backup-job-run-by-lambda)

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
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "*"
        }
    ]
}
```

Next create an IAM role also called "ebs-backup-worker" select "AWS Lambda" as the Role type, then attach the "ebs-backup-worker" policy created above. When completed and you check the trust relationship in the role through "Edit Trust Relationship" it should look like below:

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

## Add the regions you want run the scripts against as a Python Base64 encoded string Lambda environment variable "aws_regions".

Since Lambda does not allow commas in the environment variable values, we cannot enter in a list for our regions we want to run the script against. To work around this we will Base64 encode the list/string, and then decode the string in our script and then "split" the string into a list again.

Below is an example of using Python to Base64 encode our string:

```
~$ python
Python 2.7.12 (default, Nov 19 2016, 06:48:10)
[GCC 5.4.0 20160609] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import base64
>>> encoded = base64.b64encode(b'us-west-2,us-east-2')
>>> encoded
'dXMtd2VzdC0yLHVzLWVhc3QtMg=='
>>> data = base64.b64decode(encoded)
>>> data
'us-west-2,us-east-2'
>>>
```
**We will copy the encoded value and add it as the Lambda environment variable "aws_regions". When copying the encoded value please omit the single quotes in the output (ie. dXMtd2VzdC0yLHVzLWVhc3QtMg==).**

## Add the SNS Topics ARN you want publish as a Lambda environmenet variable "aws_sns_arn"

This is optional environment variable if you want publish any topic, so you might receive email notification
once backing up was executed.

## Create the Lambda Functions

Create two functions in Lambda using the Python 2.7 runtime, one for the backup script and one for the cleanup script. I recommend just using the 128 MB memory setting, and adjust the timeout to 10 seconds (longer in a larger environment). Set the event source to be "CloudWatch Events - Schedule" and set the Schedule expression to be a cron expression of your liking i.e. "cron(0 6 * * ? *)" if you want the job to be kicked off at 06:00 UTC, set the cleanup job to run a few minutes later.

## More Info

[Again if you need more details on setting this up please check my blog post.] (http://www.evergreenitco.com/evergreenit-blog/2016/4/19/aws-ebs-backup-job-run-by-lambda)
