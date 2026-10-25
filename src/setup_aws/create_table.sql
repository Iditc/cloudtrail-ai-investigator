-- Run these two statements in the Athena console (Query editor), one at a time.
-- Replace YOUR_BUCKET with the S3_BUCKET value from your .env file.

-- 1. Database
CREATE DATABASE IF NOT EXISTS cloudtrail_detective;

-- 2. Table over the raw CloudTrail files (standard AWS CloudTrail schema)
CREATE EXTERNAL TABLE IF NOT EXISTS cloudtrail_detective.cloudtrail_logs (
    eventVersion        STRING,
    userIdentity        STRUCT<
                            type: STRING,
                            principalId: STRING,
                            arn: STRING,
                            accountId: STRING,
                            invokedBy: STRING,
                            accessKeyId: STRING,
                            userName: STRING,
                            sessionContext: STRUCT<
                                attributes: STRUCT<mfaAuthenticated: STRING, creationDate: STRING>,
                                sessionIssuer: STRUCT<type: STRING, principalId: STRING, arn: STRING,
                                                      accountId: STRING, userName: STRING>>>,
    eventTime           STRING,
    eventSource         STRING,
    eventName           STRING,
    awsRegion           STRING,
    sourceIpAddress     STRING,
    userAgent           STRING,
    errorCode           STRING,
    errorMessage        STRING,
    requestParameters   STRING,
    responseElements    STRING,
    additionalEventData STRING,
    requestId           STRING,
    eventId             STRING,
    resources           ARRAY<STRUCT<arn: STRING, accountId: STRING, type: STRING>>,
    eventType           STRING,
    apiVersion          STRING,
    readOnly            STRING,
    recipientAccountId  STRING,
    serviceEventDetails STRING,
    sharedEventID       STRING,
    vpcEndpointId       STRING
)
ROW FORMAT SERDE 'com.amazon.emr.hive.serde.CloudTrailSerde'
STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://YOUR_BUCKET/cloudtrail/';

-- 3. Smoke test: the 10 most common event types
SELECT eventName, COUNT(*) AS n
FROM cloudtrail_detective.cloudtrail_logs
GROUP BY eventName
ORDER BY n DESC
LIMIT 10;
