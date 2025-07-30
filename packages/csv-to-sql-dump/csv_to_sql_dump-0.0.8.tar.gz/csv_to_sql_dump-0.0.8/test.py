
from src.csv_to_sql_dump import csv_to_sql_dump

# do stuff with csv_to_sql_dump
csv_to_sql_dump("dogs.csv", "dogs", "testdb", "dump.sql", parse_dates=["dob"])