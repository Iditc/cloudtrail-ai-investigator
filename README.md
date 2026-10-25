# CloudTrail AI Investigator

An AI agent that answers natural-language questions about AWS CloudTrail logs.
It writes SQL, runs it on Athena, explains suspicious events with RAG, and is exposed to Claude Desktop through MCP.

Learning project covering: Agents, AWS (S3, Athena, IAM, Bedrock), MCP, LLM, RAG, and a vector DB.

> Work in progress. Results, diagram and demo will be added as the project progresses.

## Data

Public CloudTrail logs from [flaws.cloud](http://flaws.cloud) by Summit Route
(20 files, 1,939,207 real events from 2017, including attack attempts).

## Progress

- [ ] Day 1: AWS setup, logs in S3, Athena table
