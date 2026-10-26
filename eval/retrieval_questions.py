"""Retrieval test set: search queries and the chunk ids that answer them.

A query counts as a hit when at least one of its relevant chunks is returned.
Chunk ids: '<doc file>:<section heading>' for knowledge docs, 'mitre:<technique id>' for ATT&CK.
"""
IDENTITIES = "dataset_context:Who the identities are"
FLAWS = "dataset_context:What flaws.cloud is"
KEYS = "dataset_context:Access key prefixes"
ERRORS = "cloudtrail_events:Error codes"
LOGGING = "cloudtrail_events:Tampering with logging (defense evasion)"
RECON = "cloudtrail_events:Reconnaissance with stolen credentials (discovery)"
ABUSE = "cloudtrail_events:Resource abuse"
AGENTS = "cloudtrail_events:User agents"

RETRIEVAL_QUESTIONS = [
    {"query": "Who is the root user in this dataset?", "relevant": [IDENTITIES]},
    {"query": "Were the Level6 keys stolen, or given to challenge players?", "relevant": [IDENTITIES]},
    {"query": "What does the user name HIDDEN_DUE_TO_SECURITY_REASONS mean?", "relevant": [IDENTITIES]},
    {"query": "What is flaws.cloud?", "relevant": [FLAWS]},
    {"query": "What is the difference between AKIA and ASIA access keys?", "relevant": [KEYS]},
    {"query": "What does the RequestLimitExceeded error mean?", "relevant": [ERRORS]},
    {"query": "What does Client.DryRunOperation mean?", "relevant": [ERRORS]},
    {"query": "Does AccessDenied mean the call failed?", "relevant": [ERRORS]},
    {"query": "An attacker called StopLogging to hide their activity", "relevant": [LOGGING, "mitre:T1685.002"]},
    {"query": "Which MITRE technique covers deleting a CloudTrail trail?", "relevant": ["mitre:T1685.002", LOGGING]},
    {"query": "Thousands of RunInstances calls with stolen keys, probably cryptocurrency mining",
     "relevant": [ABUSE, "mitre:T1496", "mitre:T1496.001"]},
    {"query": "Someone launched many EC2 instances with compromised credentials",
     "relevant": [ABUSE, "mitre:T1496", "mitre:T1496.001"]},
    {"query": "The attacker first called GetCallerIdentity to see who they are", "relevant": [RECON]},
    {"query": "Enumerating which IAM permissions the stolen keys have",
     "relevant": [RECON, "mitre:T1087.004", "mitre:T1069.003"]},
    {"query": "Searching for public EBS disk snapshots", "relevant": [RECON, "mitre:T1580"]},
    {"query": "Listing S3 buckets and checking their ACL permissions", "relevant": [RECON, "mitre:T1619"]},
    {"query": "What does 'kali' in the user agent mean?", "relevant": [AGENTS]},
    {"query": "Attacker logs in with valid stolen cloud account credentials", "relevant": ["mitre:T1078.004"]},
]
