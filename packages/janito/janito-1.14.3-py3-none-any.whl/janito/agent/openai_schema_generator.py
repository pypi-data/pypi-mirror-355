"""
Generates OpenAI-compatible function schemas from Python callables and class docstrings.

- Ensures all parameters are documented and type-annotated.
- Integrates return documentation into the schema description.
- Supports Google, NumPy, and relaxed docstring formats.
"""

import inspect
import re
import typing
from collections import OrderedDict

PYTHON_TYPE_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


class OpenAISchemaGenerator:
    """
    Generates OpenAI-compatible function schemas from Python callables and class docstrings.

    - Ensures all parameters are documented and type-annotated.
    - Integrates return documentation into the schema description.
    - Supports Google, NumPy, and relaxed docstring formats.
    """

    def __init__(self):
        pass

    def type_to_json_schema(self, annotation):
        if hasattr(annotation, "__origin__"):
            if annotation.__origin__ is list or annotation.__origin__ is typing.List:
                return {
                    "type": "array",
                    "items": self.type_to_json_schema(annotation.__args__[0]),
                }
            if annotation.__origin__ is dict or annotation.__origin__ is typing.Dict:
                return {"type": "object"}
        return {"type": PYTHON_TYPE_TO_JSON.get(annotation, "string")}

    def parse_param_section(self, lines, param_section_headers):
        param_descs = {}
        in_params = False
        for line in lines:
            stripped_line = line.strip()
            if any(
                stripped_line.lower().startswith(h + ":") or stripped_line.lower() == h
                for h in param_section_headers
            ):
                in_params = True
                continue
            if in_params:
                m = re.match(
                    r"([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(([^)]+)\))?\s*[:\-]?\s*(.+)",
                    stripped_line,
                )
                if m:
                    param, _, desc = m.groups()
                    param_descs[param] = desc.strip()
                elif stripped_line and stripped_line[0] != "-":
                    if param_descs:
                        last = list(param_descs)[-1]
                        param_descs[last] += " " + stripped_line
            if (
                stripped_line.lower().startswith("returns:")
                or stripped_line.lower() == "returns"
            ):
                break
        return param_descs

    def parse_return_section(self, lines):
        in_returns = False
        return_desc = ""
        for line in lines:
            stripped_line = line.strip()
            if (
                stripped_line.lower().startswith("returns:")
                or stripped_line.lower() == "returns"
            ):
                in_returns = True
                continue
            if in_returns:
                if stripped_line:
                    return_desc += (" " if return_desc else "") + stripped_line
        return return_desc

    def parse_docstring(self, docstring: str):
        """
        Parses a docstring to extract summary, parameter descriptions, and return description.
        Accepts Google, NumPy, and relaxed formats.
        Returns: summary, {param: description}, return_description
        """
        if not docstring:
            return "", {}, ""
        lines = docstring.strip().split("\n")
        summary = lines[0].strip()
        param_section_headers = ("args", "arguments", "params", "parameters")
        param_descs = self.parse_param_section(lines[1:], param_section_headers)
        return_desc = self.parse_return_section(lines[1:])
        return summary, param_descs, return_desc

    def generate_schema(self, tool_class):
        """
        Generates an OpenAI-compatible function schema for a tool class.
        The tool class must have _tool_run_method and _tool_name attributes set by the tool registration decorator.
        Raises ValueError if the return type is not explicitly str or if any parameter is missing a type hint.
        """
        if not hasattr(tool_class, "_tool_run_method") or not hasattr(
            tool_class, "_tool_name"
        ):
            raise ValueError(
                "Tool class must have _tool_run_method and _tool_name attributes (set by @register_tool)."
            )
        func = tool_class._tool_run_method
        tool_name = tool_class._tool_name
        sig = inspect.signature(func)
        # Enforce explicit str return type
        if sig.return_annotation is inspect._empty or sig.return_annotation is not str:
            raise ValueError(
                f"Tool '{tool_name}' must have an explicit return type of 'str'. Found: {sig.return_annotation}"
            )
        # Enforce type hints for all parameters (except self)
        missing_type_hints = [
            name
            for name, param in sig.parameters.items()
            if name != "self" and param.annotation is inspect._empty
        ]
        if missing_type_hints:
            raise ValueError(
                f"Tool '{tool_name}' is missing type hints for parameter(s): {', '.join(missing_type_hints)}.\n"
                f"All parameters must have explicit type hints for schema generation."
            )
        # Only use the class docstring for schema generation
        class_doc = (
            tool_class.__doc__.strip() if tool_class and tool_class.__doc__ else ""
        )
        summary, param_descs, return_desc = self.parse_docstring(class_doc)
        description = summary
        if return_desc:
            description += f"\n\nReturns: {return_desc}"
        # Check that all parameters in the signature have documentation
        undocumented = [
            name
            for name, param in sig.parameters.items()
            if name != "self" and name not in param_descs
        ]
        if undocumented:
            raise ValueError(
                f"Tool '{tool_name}' is missing docstring documentation for parameter(s): {', '.join(undocumented)}.\n"
                f"Parameter documentation must be provided in the Tool class docstring, not the method docstring."
            )
        properties = OrderedDict()
        required = []
        # Inject tool_call_reason as the first required parameter, unless --ntt is set
        from janito.agent.runtime_config import runtime_config

        if not runtime_config.get("no_tools_tracking", False):
            properties["tool_call_reason"] = {
                "type": "string",
                "description": "The reason or context for why this tool is being called. This is required for traceability.",
            }
            required.append("tool_call_reason")
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            annotation = param.annotation
            pdesc = param_descs.get(name, "")
            schema = self.type_to_json_schema(annotation)
            schema["description"] = pdesc
            properties[name] = schema
            if param.default == inspect._empty:
                required.append(name)
        return {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
