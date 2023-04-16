import datetime
import boto3
import logging
import os
import json
from calendar import monthrange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_secret():
    """Retrieves the sensitive variables stored in AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')

    get_secret_value_response = client.get_secret_value(
        SecretId=os.getenv('SECRET_NAME')
    )
    secrets_data = json.loads(get_secret_value_response['SecretString'])
    return secrets_data


def retention_plan_snapshot_should_be_deleted(plan, snapshot_date):
    age_in_days = (datetime.date.today() - snapshot_date).days

    if plan == 'standard':
        # Keep daily snapshots for 42 days
        return age_in_days >= 42
    elif plan == 'gold':
        # Keep daily snapshots for 42 days
        if age_in_days <= 42:
            return False
        # Keep the last snapshot of each month
        last_day_of_month = snapshot_date.replace(day=monthrange(snapshot_date.year, snapshot_date.month)[1])
        last_snapshot_of_month = snapshot_date == last_day_of_month

        smaller_than_year = age_in_days < 365

        if last_snapshot_of_month and smaller_than_year:
            return False
        else:
            return True

    elif plan == 'platinum':
        # Keep daily snapshots for 42 days
        if age_in_days <= 42:
            return False

        # Keep the last snapshot of each month
        last_day_of_month = snapshot_date.replace(day=monthrange(snapshot_date.year, snapshot_date.month)[1])
        last_snapshot_of_month = snapshot_date == last_day_of_month

        bigger_than_year = age_in_days > 365

        if bigger_than_year:
            last_seven_year_day = False

            for i in range(1, 8):
                year = datetime.date.today().year - i
                last_year_day = datetime.date(year, 12, 31)
                if snapshot_date == last_year_day:
                    last_seven_year_day = True

            if last_snapshot_of_month and last_seven_year_day:
                return False
            else:
                return True

        if last_snapshot_of_month:
            return False
        else:
            return True

    else:
        raise ValueError('Invalid retention plan')


def delete_snapshots_with_expired_retention_plan(plan):
    credentials = get_secret()

    aws_access_key = credentials['aws_access_key_id']
    aws_secret_access = credentials['aws_secret_access_key']
    aws_region = credentials['aws_region']
    volume_id = credentials['volume_id']

    # Create a boto3 EC2 client object using your AWS credentials and region
    ec2_client = boto3.client('ec2', aws_access_key_id=aws_access_key,
                              aws_secret_access_key=aws_secret_access,
                              region_name=aws_region)

    # Get all snapshots associated with the volume
    snapshots = ec2_client.describe_snapshots(Filters=[
        {'Name': 'volume-id', 'Values': [volume_id]},
    ])['Snapshots']

    # Delete expired snapshots
    for snapshot in snapshots:
        snapshot_date = snapshot['StartTime']
        if retention_plan_snapshot_should_be_deleted(plan, snapshot_date):
            snapshot_id = snapshot['SnapshotId']
            logger.info(f'Deleting snapshot {snapshot_id} (taken on {snapshot_date})...')
            ec2_client.delete_snapshot(SnapshotId=snapshot_id)


if __name__ == '__main__':

    delete_snapshots_with_expired_retention_plan('platinum')
