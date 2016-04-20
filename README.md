# aws-lambda-ebs-backups
Python scripts to be run using AWS's Lambda service to Backup and Delete Snapshots of EBS Volumes

Read my blog post for more details on setting this up in Lambda if you have not used it before (http://www.evergreenitco.com/evergreenit-blog/2016/4/19/aws-ebs-backup-job-run-by-lambda).

## Setting Up IAM Permissions

First create an IAM policy called "ebs-backup-worker" with the following policy document:

<script src="https://gist.github.com/cmachler/5da68479e53fd9f9247b74349046ad19.js"></script>
