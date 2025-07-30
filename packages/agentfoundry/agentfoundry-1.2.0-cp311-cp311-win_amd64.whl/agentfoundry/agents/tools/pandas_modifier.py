import json
import traceback

import pandas as pd
from langchain_core.tools import Tool


def modify_csv(input_str: str) -> str:
    """
    Synchronously loads the CSV at `file_path`, execute `code` against a local namespace where `df`
    is the DataFrame, then write the modified DataFrame back to `file_path`.
    """
    try:
        data = json.loads(input_str)
        file_path = data.get("file_path", None)
        code = data.get("code", None)
        if code is None or file_path is None:
            return "No code or file path provided."
        # 1. Read the CSV into a pandas DataFrame
        df = pd.read_csv(file_path)

        # 2. Prepare a local namespace so the user's code can reference 'df'
        local_vars = {"df": df}

        # 3. Execute the user‐provided code snippet
        #    Example: code could be "df['new_col'] = df['old_col'] * 2"
        exec(code, globals(), local_vars)

        # 4. Retrieve the possibly modified DataFrame (fallback to original if they never reassigned)
        df_modified = local_vars.get("df", df)

        # 5. Overwrite the CSV file with the updated DataFrame
        new_path = file_path.replace(".csv", "_new.csv")
        df_modified.to_csv(new_path, index=False)

        return f"Successfully modified '{new_path}'."
    except Exception as e:
        # Capture the full traceback for easier debugging
        tb = traceback.format_exc()
        return f"Error modifying CSV: {e}\n{tb}"


csv_modifier_tool = Tool(
    name="modify_csv",
    func=modify_csv,
    description=(
        "Loads a CSV file and modifies it using code that is provided."
        "Input must be a JSON string with keys 'file_path' (a string path to a CSV file) and 'code' which contains a "
        "string of Python code to be executed on the CSV file. This function will load the CSV into a pandas DataFrame "
        "(called df), execute the code (which should modify df in‐place or reassign it), then save "
        "the new CSV with the result. Returns a success message or an error."
    )
)