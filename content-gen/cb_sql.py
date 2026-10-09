from cb_common import build
from cb_sql_notes import NOTES
from cb_sql_qa import QA
SOURCES = [
 ("MySQL 8.4 Reference Manual", "https://dev.mysql.com/doc/refman/8.4/en/"),
 ("MySQL - InnoDB Locking", "https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html"),
 ("MySQL - Transaction Isolation Levels", "https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html"),
 ("MySQL - InnoDB Multi-Versioning", "https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html"),
 ("MySQL - EXPLAIN Output Format", "https://dev.mysql.com/doc/refman/8.4/en/explain-output.html"),
 ("MySQL - Window Functions", "https://dev.mysql.com/doc/refman/8.4/en/window-functions.html"),
 ("Use The Index, Luke (Markus Winand)", "https://use-the-index-luke.com/"),
 ("LeetCode - Top SQL 50", "https://leetcode.com/studyplan/top-sql-50/"),
 ("GeeksforGeeks - SQL Interview Questions", "https://www.geeksforgeeks.org/sql/sql-interview-questions/"),
 ("InterviewBit - SQL Interview Questions", "https://www.interviewbit.com/sql-interview-questions/"),
]
build("sql", "SQL & MySQL", 4, "🗄️", "SQL querying, window functions, indexing, query optimization, transactions, locking and MySQL scaling.", NOTES, QA, SOURCES)
