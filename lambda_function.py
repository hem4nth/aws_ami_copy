import json
import boto3
import csv
import datetime
from dateutil.tz import tzutc
import re
import botocore.exceptions
import os
SOURCE_REGION = 'eu-west-1'
source_client  = boto3.client('ec2', region_name=SOURCE_REGION)

# Function for getting Ec2 and their instance details
def copy_ami(accountsList):
    # List of Regions where EC2 instances are deployed
    RegionList = ["eu-west-1", "eu-central-1"]

    for id in accountsList:
      # Getting the Account IDs

        # Assume Role for respective accounts
        sts_client = boto3.client('sts')
        assumeRole = sts_client.assume_role(
            RoleArn="arn:aws:iam::" + id + ":role/AWSCloudFormationStackSetExecutionRole",
            RoleSessionName="AssumeRoleSession1")
        creds = assumeRole['Credentials']
        images = source_client.describe_images(Filters=[{'Name':'tag:share', 'Values':['true']}])
        for ami in images['Images']:
            if 'Tags' in ami:
                name = [tag['Value'] for tag in ami['Tags'] if tag['Key'] == 'Name'][0]
            else:
                 name = ''
            print (name, ami['Name'], ami['ImageId'], ami['State'])
            
            for region in RegionList:
                ec2Object = boto3.client('ec2', aws_access_key_id=creds['AccessKeyId'],
                                         aws_secret_access_key=creds['SecretAccessKey'],
                                         aws_session_token=creds['SessionToken'], region_name=region)
                ec2Object.copy_image(
                    Description='test',
                    Encrypted=False,
                    Name='amishare',
                    SourceImageId=ami['ImageId'],
                    SourceRegion=SOURCE_REGION,
                )
                print ('Copied Image ID is ' + response['ImageId'])

def accounts_list():
    accountsList, activeAccountsList = ([] for i in range(2))
    
    # Listing the AWS accounts under the organization in Dev
    orgs = boto3.client('organizations')
    resp = orgs.list_accounts()
    accountsList = resp['Accounts']
    while 'NextToken' in resp:
        resp = orgs.list_accounts(NextToken=resp['NextToken'])
        accountsList.extend(resp['Accounts'])
    print("Total number of accounts : ", len(accountsList))
    
    for account in accountsList:
        if account['Status'] == 'ACTIVE':
            activeAccountsList.append(account["Id"])
            print(account)
    
    return activeAccountsList
    
    
def lambda_handler(event, context):
    activeAccountsList = accounts_list()
    copy_ami(activeAccountsList)  # Function call

