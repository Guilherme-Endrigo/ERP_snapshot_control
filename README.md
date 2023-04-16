# ERP_snapshot_control

The code implementing a snapshot retention policy for AWS EC2 snapshots. It uses a function named retention_plan_snapshot_should_be_deleted to determine whether a snapshot should be deleted based on the retention plan of the snapshot, and another function named delete_snapshots_with_expired_retention_plan to delete all snapshots that have expired based on their retention plan.

The retention plan for each snapshot is determined based on a classification of 'standard', 'gold', or 'platinum'. Each plan has different retention policies:

Standard: Keep daily snapshots for 42 days
Gold: Keep daily snapshots for 42 days, keep the last snapshot of each month for up to one year
Platinum: Keep daily snapshots for 42 days, keep the last snapshot of each month for up to one year, keep the last snapshot of each year for up to 7 years.
The retention_plan_snapshot_should_be_deleted function takes two arguments, the retention plan of the snapshot, and the date the snapshot was taken. It then calculates the age of the snapshot and returns True if the snapshot should be deleted, based on the retention policy for that plan.

The delete_snapshots_with_expired_retention_plan function retrieves the retention plan, AWS credentials, region, and volume ID from AWS Secrets Manager. It then creates an EC2 client object using the credentials and region, and uses it to retrieve all snapshots associated with the specified volume. It then iterates over the snapshots, and calls retention_plan_snapshot_should_be_deleted to determine whether each snapshot should be deleted. If the snapshot should be deleted, it calls the delete_snapshot method of the EC2 client to delete it.

The code also includes a test suite that tests and mock AWS usage.

##Use -
to start the project it is necessary to install the libraries contained in requirements.txt and replace the secret values in get_secret()
