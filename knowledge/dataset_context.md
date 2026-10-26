# Dataset context: flaws.cloud CloudTrail logs

## What flaws.cloud is
flaws.cloud is a public security challenge (CTF) built by Scott Piper of Summit Route.
It is an AWS account (account ID 811596193553) set up with deliberate security weaknesses
across six levels, so people can practice attacking AWS. The CloudTrail logs of this account
were later published as a dataset. They cover February 2017 to October 2020 and contain
activity from many different challenge players and automated scanners, not from a single attacker.
Because the account exists to be attacked, a lot of suspicious-looking activity is expected.

## Who the identities are
- Root user "flaws": the account owner. Administrative actions by Root, such as CreateTrail,
  StartLogging, UpdateTrail or DeleteTrail, are most likely the owner maintaining the account.
  They are not automatically malicious, but should still be verified.
- IAM users "Level6" and "backup": their access keys were intentionally exposed to players as
  part of the challenge. Activity by these users comes from challenge players or attackers who
  found the keys, not from the owner.
- IAM user "piper": most likely the challenge creator.
- IAM user "SecurityMokey": most likely the owner's monitoring tool (Netflix Security Monkey).
- userName "HIDDEN_DUE_TO_SECURITY_REASONS": CloudTrail hides the user name when a console
  sign-in fails with a user name that does not exist, to avoid logging mistyped passwords.

## Access key prefixes
- Keys starting with AKIA are long-term access keys of an IAM user or root.
- Keys starting with ASIA are temporary credentials issued by AWS STS (assumed roles, console sessions).
