# How to read CloudTrail events

## Error codes
- errorCode NULL (empty) means the call succeeded.
- AccessDenied and Client.UnauthorizedOperation: the caller does not have IAM permission for the action.
- Client.RequestLimitExceeded: AWS throttled the caller for sending too many API requests too fast.
  Large numbers of these usually mean an automated script, not a person.
- Client.InstanceLimitExceeded and Client.VcpuLimitExceeded: the account hit its service quota for instances or vCPUs.
- Server.InsufficientInstanceCapacity: AWS did not have enough capacity for the requested instance type in that zone.
- Client.Unsupported: the requested configuration (for example an instance type) is not supported where it was requested.
- Client.DryRunOperation: the call would have succeeded. It is returned when DryRun is set, and is often used
  to quietly test permissions without launching anything.

## Tampering with logging (defense evasion)
StopLogging, DeleteTrail, UpdateTrail and PutEventSelectors can disable or reduce CloudTrail logging.
An attacker uses them to hide their activity. This maps to MITRE ATT&CK T1685.002
(Disable or Modify Cloud Log; formerly T1562.008, which MITRE has revoked). DescribeTrails, GetTrailStatus and GetEventSelectors
only read the logging configuration; an attacker uses them to check whether they are being recorded.

## Reconnaissance with stolen credentials (discovery)
- GetCallerIdentity ("who am I?") is often the first call made with stolen keys.
- GetPolicyVersion, ListAttachedUserPolicies and ListEntitiesForPolicy enumerate what the keys are allowed to do.
- ListBuckets and GetBucketAcl look for S3 buckets and who can access them.
- DescribeInstances, DescribeSnapshots and DescribeSnapshotAttribute map servers and disk snapshots;
  DescribeSnapshotAttribute shows whether a snapshot is shared or public.
- Calls spread across many unrelated services in a short time usually come from automated enumeration tools.

## Resource abuse
A burst of RunInstances calls, often together with DescribeSpotPriceHistory, is a common sign that stolen keys
are being used to launch servers for cryptocurrency mining. This maps to MITRE ATT&CK T1496 (Resource Hijacking).

## User agents
- console.amazonaws.com or names like [S3Console]: a person using the AWS web console.
- aws-cli/...: the AWS command line tool. boto3 or botocore: a Python script.
- "kali" inside the user agent: Kali Linux, an operating system built for penetration testing.
