# CloudTrail AI Investigator

An AI agent that answers natural-language questions about AWS CloudTrail logs.
It writes SQL, runs it on Athena, explains suspicious events with RAG, and is exposed to Claude Desktop through MCP.

Learning project covering: Agents, AWS (S3, Athena, IAM, Bedrock), MCP, LLM, RAG, and a vector DB.

> Work in progress. Results, diagram and demo will be added as the project progresses.

## Project goal

This is **not** an anomaly detection model, and the data has **no labels**.
It is an assistant for a security investigator.

When an alert fires in a SOC, an investigator has to reconstruct what happened:
who did what, when, from where, and whether it worked. Today that means writing
long SQL queries by hand and looking up error codes in the documentation.

The agent does this work. The investigator asks in plain English, for example
*"Did anyone try to turn off CloudTrail logging?"*, and the agent writes the SQL,
runs it on Athena, and explains the result with security context.

**How it is evaluated without labels:** a set of test questions, each with an
expected answer computed independently in pandas. The agent is scored on whether
it reaches the same answer. These question-answer pairs play the role of labels.

## Data

Public CloudTrail logs from [flaws.cloud](http://flaws.cloud) by Summit Route
(20 files, 1,939,207 real events from Feb 2017 to Oct 2020, including attack attempts).

flaws.cloud is a public security challenge (CTF): an AWS account built with
deliberate weaknesses so people can practice attacking it. The logs therefore
contain activity from many players and automated scanners over several years,
not from a single attacker.

### Anatomy of one event

Every CloudTrail event answers five questions. Example: a `StopLogging` attempt.

| Question | Columns | Example value |
|---|---|---|
| Who? | `identityType`, `userName`, `accessKeyId` | IAM user `Level6`, permanent key (`AKIA...`) |
| Did what? | `eventName`, `eventSource` | `StopLogging` on `cloudtrail.amazonaws.com` |
| When? | `eventTime` (UTC) | 2019-06-07 11:04:25 |
| From where? | `sourceIPAddress`, `userAgent` | `2.251.2.5`, AWS CLI on Linux |
| Did it work? | `errorCode`, `errorMessage` | `AccessDenied` (empty means success) |

**Reading it:** a player who obtained the level 6 keys of the challenge tried to
turn off logging to hide their tracks, and was blocked. By contrast, a successful
`DeleteTrail` by the `Root` identity two months later was most likely the account
owner doing maintenance. The same kind of action means different things depending
on *who* did it and *whether it succeeded*.

## Progress

- [ ] Day 1: AWS setup, logs in S3, Athena table
