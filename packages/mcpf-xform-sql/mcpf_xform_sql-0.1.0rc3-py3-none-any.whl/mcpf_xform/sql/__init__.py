from typing import Any

import duckdb
import mcpf_core.core.routines as routines
from mcpf_core.func import constants


def df_sql_statement(data: dict[str, Any]) -> dict[str, Any]:
    """Executes a SQL query on a given pandas DataFrame and returns the transformed DataFrame.

    This function reads a pandas DataFrame (`df`) and a SQL query (`query`), applies the SQL query
    on the DataFrame, and returns a new DataFrame containing the results of the query.

    Args:
        data (dict[str, Any]): _description_

    Returns:
        dict[str, Any]: _description_
    """
    # general code part 2/1
    iterator = routines.pop_loop_iterator()
    meta = routines.get_meta_data(data)
    # default_arguments_values
    arg = {
        "input": constants.DEFAULT_IO_DATA_LABEL,
        "output": constants.DEFAULT_IO_DATA_LABEL,
        "query": "",
        "query_encoding": "",
        "is_literal_query": True,
    }
    # merging default values with current argument values
    if meta[constants.ARGUMENTS]:
        arg = arg | meta[constants.ARGUMENTS]
    # if the function part of a loop
    if iterator:
        arg["input"] = iterator

    if data[arg["input"]] is None:
        data[arg["output"]] = data[arg["input"]]
    else:
        # create DuckDB connection
        conn = duckdb.connect(database=":memory:")
        conn.register("data", data[arg["input"]])

        if arg["is_literal_query"]:
            query: str = arg["SQL_STMT"] if not arg["query"] and "SQL_STMT" in arg else arg["query"]
        else:
            query: str = data[arg["SQL_STMT"] if not arg["query"] and "SQL_STMT" in arg else arg["query"]]
        if arg["query_encoding"]:
            # It looks like the lasagna package decodes some unicode strings
            # to a utf-8 representation wrapped by a python unicode string.
            # It seems to do this only under windows.
            # Therefore, we attempt to interpret the query string as utf-8 first,
            # and if decoding fails, we assume it to be already a utf-8 string.
            try:
                query = query.encode(arg["query_encoding"]).decode("utf-8")
            except UnicodeDecodeError:
                pass

        df = conn.execute(query).fetchdf()

        data[arg["output"]] = df
        routines.set_meta_in_data(data, meta)
        return data
