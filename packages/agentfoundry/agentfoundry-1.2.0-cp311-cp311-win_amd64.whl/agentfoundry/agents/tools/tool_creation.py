from langchain_core.tools import Tool
import traceback
import re
import os
import json


def create_python_tool(input_str: str) -> str:
    """Saves new Python code as a Tool."""
    try:
        data = json.loads(input_str)
        result = data.get("code")
        tool_name = data.get("name")
    except Exception as e:
        return f"Error parsing input JSON: {e}"
    match = re.search(r"```(?:python)?\s*([\s\S]*?)```", result)
    result = match.group(1) if match else result
    try:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(module_dir, f"{tool_name}.py")
        with open(file_path, "w") as file:
            file.write(result)
        return f"Created new tool: {tool_name}."
    except Exception as e:
        tb = traceback.format_exc()
        return f"Error creating new Tool: {e}\n{tb}"


tool_creation = Tool(
    name="python_tool_creator",
    func=create_python_tool,
    description=(
        "This tool takes in a string input that must be a JSON string with keys 'name' for the new tool's name and "
        "'code' which contains the new Python code tool to be saved. The new tool will be used by an Agentic AI. Make "
        "sure that the input string contains all necessary imports "
        "including 'from langchain_core.tools import Tool'. Additionally, the inputs to the function need to be "
        "strings and if multiple inputs are required, then a single JSON string with multiple keys will be the "
        "Tool's input argument. Lastly, the code must include the following example at the end: "
        """
        example_tool = Tool(
        name="new_tool_name",
        func=function_name,
        description=(
            "description of how the new function works including what should be in the function parameter, i.e. a 
            string, or a JSON string with multiple keys."
        )
        )
        """
        "Be careful when generating code using f-strings and be conscious of the single and double quotation marks."
        "This is a very sensitive tool - do not create any malicious tool or any code that can compromise the system. "
    )
)