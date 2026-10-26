"""The 20 evaluation questions and how to compute their expected answers.

Each question has a function that computes the facts a correct answer must
contain, straight from the data with pandas (never typed by hand). A fact is a
list of acceptable spellings, e.g. a date as '2019-08-22' or 'August 22, 2019'.
"""
import pandas as pd

NUMBER_WORDS = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def num(n: int) -> list[str]:
    """Acceptable spellings of a whole number (digits, plus a word if small)."""
    n = int(n)
    return [str(n)] + ([NUMBER_WORDS[n]] if n in NUMBER_WORDS else [])


def date(value) -> list[str]:
    """Acceptable spellings of a calendar date."""
    d = pd.Timestamp(value)
    return [d.strftime("%Y-%m-%d"), f"{d:%B} {d.day}, {d.year}", f"{d.day} {d:%B} {d.year}",
            f"{d:%b} {d.day}, {d.year}", f"{d.day} {d:%b} {d.year}"]


def text(value: str) -> list[str]:
    """Acceptable spellings of a name, IP or code, including common short forms
    ('RequestLimitExceeded' for 'Client.RequestLimitExceeded', 'ec2' for 'ec2.amazonaws.com')."""
    value = str(value)
    variants = [value]
    for prefix in ("Client.", "Server."):
        if value.startswith(prefix):
            variants.append(value.removeprefix(prefix))
    if value.endswith(".amazonaws.com"):
        variants.append(value.removesuffix(".amazonaws.com"))
    return variants


def month(value: str) -> list[str]:
    """Acceptable spellings of a calendar month given as 'YYYY-MM'."""
    d = pd.Timestamp(f"{value}-01")
    return [value, f"{d:%B} {d.year}", f"{d:%b} {d.year}"]


def hour(h: int) -> list[str]:
    """Acceptable spellings of an hour of the day (e.g. 7, '07:00')."""
    return [str(h), f"{h:02d}", f"{h:02d}:00", f"{h}:00"]


def top(series: pd.Series):
    """Most frequent value of a series and its count."""
    counts = series.astype(str).value_counts()
    return counts.index[0], counts.iloc[0]


def run_instances(df: pd.DataFrame) -> pd.DataFrame:
    """Only the RunInstances events."""
    return df[df["eventName"] == "RunInstances"]


def peak_day(df: pd.DataFrame):
    """Day with the most RunInstances calls."""
    return run_instances(df)["eventTime"].dt.date.value_counts().idxmax()


def first_event_of_top_ip(df: pd.DataFrame) -> pd.Series:
    """First event (by time) of the IP that made the most RunInstances calls."""
    ip = top(run_instances(df)["sourceIPAddress"])[0]
    return df[df["sourceIPAddress"] == ip].sort_values("eventTime").iloc[0]


def stoplogging_ip(df: pd.DataFrame) -> str:
    """The source IP of the StopLogging attempts."""
    return top(df[df["eventName"] == "StopLogging"]["sourceIPAddress"])[0]


QUESTIONS = [
    # General
    {"id": "q01", "topic": "general",
     "question": "How many events are in the CloudTrail logs in total?",
     "facts": lambda df: [num(len(df))]},
    {"id": "q02", "topic": "general",
     "question": "What is the date range of the logs (first and last event)?",
     "facts": lambda df: [date(df["eventTime"].min()), date(df["eventTime"].max())]},
    {"id": "q03", "topic": "general",
     "question": "Which AWS service (event source) has the most events?",
     "facts": lambda df: [text(top(df["eventSource"])[0])]},
    {"id": "q04", "topic": "general",
     "question": "What is the most common API action (event name)?",
     "facts": lambda df: [text(top(df["eventName"])[0])]},
    {"id": "q05", "topic": "general",
     "question": "How many distinct source IP addresses appear in the logs?",
     "facts": lambda df: [num(df["sourceIPAddress"].nunique())]},
    # The RunInstances incident
    {"id": "q06", "topic": "runinstances",
     "question": "Which source IP address made the most RunInstances calls, and how many?",
     "facts": lambda df: [text(top(run_instances(df)["sourceIPAddress"])[0]),
                          num(top(run_instances(df)["sourceIPAddress"])[1])]},
    {"id": "q07", "topic": "runinstances",
     "question": "On which day were there the most RunInstances calls?",
     "facts": lambda df: [date(peak_day(df))]},
    {"id": "q08", "topic": "runinstances",
     "question": "How many RunInstances calls succeeded in the whole dataset?",
     "facts": lambda df: [num(run_instances(df)["errorCode"].isna().sum())]},
    {"id": "q09", "topic": "runinstances",
     "question": "What is the most common error code for RunInstances calls?",
     "facts": lambda df: [text(top(run_instances(df)["errorCode"].dropna())[0])]},
    {"id": "q10", "topic": "runinstances",
     "question": "Which IAM users made RunInstances calls on the peak day of RunInstances activity?",
     "facts": lambda df: [text(u) for u in sorted(
         run_instances(df)[run_instances(df)["eventTime"].dt.date == peak_day(df)]["userName"].dropna().unique())]},
    # Identities
    {"id": "q11", "topic": "identities",
     "question": "Which IAM user made the most API calls, and how many?",
     "facts": lambda df: [text(top(df[df["identityType"] == "IAMUser"]["userName"].dropna())[0]),
                          num(top(df[df["identityType"] == "IAMUser"]["userName"].dropna())[1])]},
    {"id": "q12", "topic": "identities",
     "question": "How many events were made by the root user (identity type Root)?",
     "facts": lambda df: [num((df["identityType"] == "Root").sum())]},
    {"id": "q13", "topic": "identities",
     "question": "How many events have the user name HIDDEN_DUE_TO_SECURITY_REASONS?",
     "facts": lambda df: [num((df["userName"] == "HIDDEN_DUE_TO_SECURITY_REASONS").sum())]},
    # Logging tampering
    {"id": "q14", "topic": "logging",
     "question": "Who called StopLogging, and did it succeed?",
     "facts": lambda df: [text(top(df[df["eventName"] == "StopLogging"]["userName"].dropna())[0]),
                          text(top(df[df["eventName"] == "StopLogging"]["errorCode"].dropna())[0])]},
    {"id": "q15", "topic": "logging",
     "question": "Which identity deleted a CloudTrail trail (DeleteTrail) successfully, and on what date?",
     "facts": lambda df: [text(df[(df["eventName"] == "DeleteTrail") & df["errorCode"].isna()]["identityType"].iloc[0]),
                          date(df[(df["eventName"] == "DeleteTrail") & df["errorCode"].isna()]["eventTime"].iloc[0])]},
    # Reconnaissance
    {"id": "q16", "topic": "recon",
     "question": "How many DescribeSnapshots calls are in the logs?",
     "facts": lambda df: [num((df["eventName"] == "DescribeSnapshots").sum())]},
    {"id": "q17", "topic": "recon",
     "question": "Which user name made the most GetCallerIdentity calls?",
     "facts": lambda df: [text(top(df[df["eventName"] == "GetCallerIdentity"]["userName"].dropna())[0])]},
    {"id": "q18", "topic": "recon",
     "question": "Which source IP address received the most AccessDenied errors?",
     "facts": lambda df: [text(top(df[df["errorCode"] == "AccessDenied"]["sourceIPAddress"])[0])]},
    {"id": "q19", "topic": "recon",
     "question": "How many events came from a user agent that contains 'kali' (Kali Linux)?",
     "facts": lambda df: [num(df["userAgent"].str.contains("kali", case=False, na=False).sum())]},
    {"id": "q20", "topic": "recon",
     "question": "How many events failed (have an error code)?",
     "facts": lambda df: [num(df["errorCode"].notna().sum())]},
    # Harder questions: several steps, time logic, traps, and knowledge from RAG
    {"id": "q21", "topic": "hard_chain",
     "question": "Take the IP address that made the most RunInstances calls. When did it first appear "
                 "in the logs, which user did it use, and what was its very first action?",
     "facts": lambda df: [date(first_event_of_top_ip(df)["eventTime"]),
                          text(first_event_of_top_ip(df)["userName"]),
                          text(first_event_of_top_ip(df)["eventName"])]},
    {"id": "q22", "topic": "hard_chain",
     "question": "Which IP address called StopLogging, and how many events in total came from that IP?",
     "facts": lambda df: [text(stoplogging_ip(df)), num((df["sourceIPAddress"] == stoplogging_ip(df)).sum())]},
    {"id": "q23", "topic": "hard_chain",
     "question": "Apart from RunInstances, what was the most common action of the IAM user Level6?",
     "facts": lambda df: [text(top(df[(df["userName"] == "Level6")
                                      & (df["eventName"] != "RunInstances")]["eventName"])[0])]},
    {"id": "q24", "topic": "hard_time",
     "question": "On 2019-08-22, in which hour of the day (UTC) were there the most RunInstances calls?",
     "facts": lambda df: [hour(run_instances(df)[run_instances(df)["eventTime"].dt.date
                                                 == pd.Timestamp("2019-08-22").date()]
                               ["eventTime"].dt.hour.value_counts().idxmax())]},
    {"id": "q25", "topic": "hard_time",
     "question": "On how many distinct days (UTC) is there at least one event?",
     "facts": lambda df: [num(df["eventTime"].dt.date.nunique())]},
    {"id": "q26", "topic": "hard_time",
     "question": "Which calendar month had the most events, and how many events were in it?",
     "facts": lambda df: [month(top(df["eventTime"].dt.strftime("%Y-%m"))[0]),
                          num(top(df["eventTime"].dt.strftime("%Y-%m"))[1])]},
    {"id": "q27", "topic": "hard_trap",
     "question": "How many DeleteBucket calls succeeded?",
     "facts": lambda df: [num(((df["eventName"] == "DeleteBucket") & df["errorCode"].isna()).sum())]},
    {"id": "q28", "topic": "hard_trap",
     "question": "What exact user agent string was used for the StopLogging attempts?",
     "facts": lambda df: [text(df[df["eventName"] == "StopLogging"]["userAgent"].iloc[0].split()[0]),
                          text("kali")]},
    {"id": "q29", "topic": "hard_trap",
     "question": "Excluding throttled calls (error code RequestLimitExceeded), how many distinct "
                 "source IP addresses made RunInstances calls?",
     "facts": lambda df: [num(run_instances(df)[run_instances(df)["errorCode"].astype(str)
                                                 != "Client.RequestLimitExceeded"]["sourceIPAddress"].nunique())]},
    {"id": "q30", "topic": "hard_rag",
     "question": "In this dataset, which identity is most likely the legitimate account owner, "
                 "and which IAM users had their access keys exposed to challenge players?",
     "facts": lambda df: [text("root"), text("Level6"), text("backup")]},
]
