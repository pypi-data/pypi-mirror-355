import pandas as pd
import pathlib

def _build_df(
    target: str | pathlib.Path | pd.DataFrame,
    parse_dates: list[str] = ()
) -> pd.DataFrame:
    if isinstance(target, pd.DataFrame):
        return target
    try:
        return pd.read_csv(target, parse_dates=parse_dates)
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


def csv_to_sql_dump(
    target: str | pathlib.Path | pd.DataFrame,
    table_name: str,
    database_name: str,
    output_filepath: str = "dump.sql",
    parse_dates: list[str] = (),
) -> None:
    df = _build_df(target, parse_dates)
    lines = [
        f"DROP DATABASE IF EXISTS {database_name};",
        f"CREATE DATABASE {database_name};",
        f"USE {database_name};",
        "",
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
    insert_template = f"INSERT INTO {table_name} ({columns}) VALUES"

    for i, row in df.iterrows():
        lines.append(f"{insert_template} {tuple(row.values)};")

    with open(output_filepath, "w") as f:
        f.write("\n".join(lines))