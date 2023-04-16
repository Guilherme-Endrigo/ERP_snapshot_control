import unittest
import datetime
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from main import retention_plan_snapshot_should_be_deleted, delete_snapshots_with_expired_retention_plan


class TestRetentionPlanSnapshotShouldBeDeleted(unittest.TestCase):

    def test_standard_plan_retention(self):
        # Test daily snapshot retention for standard plan
        today = datetime.date.today()
        snapshot_date = today - datetime.timedelta(days=42)
        self.assertTrue(retention_plan_snapshot_should_be_deleted('standard', snapshot_date))
        snapshot_date = today - datetime.timedelta(days=41)
        self.assertFalse(retention_plan_snapshot_should_be_deleted('standard', snapshot_date))

    def test_gold_plan_retention(self):
        # Test daily and monthly snapshot retention for gold plan
        today = datetime.date.today()
        snapshot_date = today - datetime.timedelta(days=42)
        self.assertFalse(retention_plan_snapshot_should_be_deleted('gold', snapshot_date))
        # Last day of month
        snapshot_date = today - datetime.timedelta(days=351)
        self.assertFalse(retention_plan_snapshot_should_be_deleted('gold', snapshot_date))
        snapshot_date = today - datetime.timedelta(days=380)
        self.assertTrue(retention_plan_snapshot_should_be_deleted('gold', snapshot_date))

    def test_platinum_plan_retention(self):
        # Test daily, monthly, and 7-year snapshot retention for platinum plan
        today = datetime.date.today()
        snapshot_date = today - datetime.timedelta(days=42)
        self.assertFalse(retention_plan_snapshot_should_be_deleted('platinum', snapshot_date))
        snapshot_date = today - datetime.timedelta(days=370)
        self.assertTrue(retention_plan_snapshot_should_be_deleted('platinum', snapshot_date))
        snapshot_date = today - datetime.timedelta(days=351)
        self.assertFalse(retention_plan_snapshot_should_be_deleted('platinum', snapshot_date))
        snapshot_date = datetime.date(2018, 12, 31)
        self.assertFalse(retention_plan_snapshot_should_be_deleted('platinum', snapshot_date))
        snapshot_date = datetime.date(2010, 1, 2)
        self.assertTrue(retention_plan_snapshot_should_be_deleted('platinum', snapshot_date))


class TestDeleteSnapshotsWithExpiredRetentionPlan(unittest.TestCase):

    @patch('main.get_secret')
    def test_delete_expired_snapshots(self, mock_get_secret):
        # Set up mock credentials
        mock_credentials = {
            'aws_access_key_id': 'fake_access_key',
            'aws_secret_access_key': 'fake_secret_key',
            'aws_region': 'us-west-2',
            'volume_id': 'vol-0123456789abcdef0'
        }
        mock_get_secret.return_value = mock_credentials

        # Set up mock EC2 client and snapshots
        mock_ec2_client = MagicMock()
        mock_snapshot1 = {'SnapshotId': 'snap-0123456789abcdef0', 'StartTime': date.today() - timedelta(days=3)}
        mock_snapshot2 = {'SnapshotId': 'snap-abcdef0123456789', 'StartTime': date.today() - timedelta(days=80)}
        mock_snapshots = [mock_snapshot1, mock_snapshot2]
        mock_ec2_client.describe_snapshots.return_value = {'Snapshots': mock_snapshots}

        # Call the function with a retention plan of 2 days
        with patch('main.boto3.client', return_value=mock_ec2_client):
            delete_snapshots_with_expired_retention_plan('platinum')

        # Check that delete_snapshot() was called only for the expired snapshot
        mock_ec2_client.delete_snapshot.assert_called_once_with(SnapshotId=mock_snapshot2['SnapshotId'])


if __name__ == '__main__':
    unittest.main()
