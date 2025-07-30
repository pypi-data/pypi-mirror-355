import re
import math
import pandas as pd
import pathlib

def _build_df(
    target: str | pathlib.Path | pd.DataFrame,
    parse_dates: list[str] = ()
) -> pd.DataFrame:
    if isinstance(target, pd.DataFrame):
        return target
    try:
        return pd.read_csv(target, parse_dates=parse_dates, dayfirst=True)
    except Exception as e:
        raise ValueError(f"Invalid object passed to pd.read_csv {target}. {e}") from e


def get_sql_type_from_numpy_dtype(numpy_dtype):
    dtype = str(numpy_dtype).lower()
    if "bool" in dtype: return "BOOLEAN"
    if "int" in dtype or "long" in dtype: return "INT"
    if "float" in dtype or "double" in dtype: return "FLOAT"
    if "object" in dtype: return "VARCHAR(255)"
    if "datetime" in dtype: return "DATETIME"
    return "VARCHAR(255)"


def get_tuple(values):
    out = []
    for val in values:
        if pd.isnull(val) or pd.isna(val):
            out.append(None)
        elif type(val) in [int, float, str, bool]:
            out.append(val)
        elif re.match(".*(date|time).*", str(type(val)).lower()):
            out.append(val.strftime("%Y-%m-%d"))
        else:
            out.append(val)
    joined = ", ".join([repr(val) if val is not None else "NULL" for val in out])
    return f"({joined})"

def csv_to_sql_dump(
    target: str | pathlib.Path | pd.DataFrame,
    table_name: str,
    database_name: str,
    output_filepath: str = "dump.sql",
    parse_dates: list[str] = (),
) -> None:
    df = _build_df(target, parse_dates)
    if len(df.columns) != len(set(df.columns)):
        raise ValueError(f"Duplicated columns found: {df.columns}")

    lines = [
        f"CREATE DATABASE IF NOT EXISTS {database_name};",
        f"USE {database_name};",
        "",
        f"DROP TABLE IF EXISTS {table_name};",
        f"CREATE TABLE {table_name} ("
    ]
    if "id" not in df.columns:
        lines.append("    `id` INT PRIMARY KEY AUTO_INCREMENT,")
    for colname, coltype in zip(df.columns, df.dtypes):
        sql_type = get_sql_type_from_numpy_dtype(coltype)
        lines.append(
            f"    `{colname}` {sql_type},"
        )
    lines[-1] = lines[-1][:-1]  # remove trailing comma
    lines.append(");\n")

    # INSERT statements
    columns = ", ".join([f"`{col}`" for col in df.columns])
    lines.append(f"INSERT INTO {table_name} ({columns}) VALUES")
    for i, row in df.iterrows():
        lines.append(f"    {get_tuple(row.values)},")
    lines[-1] = lines[-1][:-1]
    lines.append(";")

    with open(output_filepath, "w") as f:
        f.write("\n".join(lines))