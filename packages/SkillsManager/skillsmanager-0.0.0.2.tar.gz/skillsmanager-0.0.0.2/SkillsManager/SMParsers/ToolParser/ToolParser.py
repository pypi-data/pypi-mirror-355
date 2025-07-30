
import os
import importlib.util
import sys
import json
import inspect
import re
import logging
from google import genai
from google.genai import types
from typing import get_type_hints
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ToolParser:

    @staticmethod
    def parseToolDocstring(docstring):
        """
        Parse the docstring of a function to extract metadata like description and additional information.
        Returns a dictionary with keys 'description' and 'additional_information'.
        """
        result = {
            "description": "",
            "additional_information": None,
        }
        if not docstring:
            return result
        lines = [line.strip() for line in docstring.strip().splitlines() if line.strip()]
        for line in lines:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.lower().replace(" ", "_")
            value = value.strip().strip('"').strip("'")
            if key in result:
                result[key] = value
        if not result["description"] and lines:
            result["description"] = lines[0]
        return result

    @staticmethod
    def getTools(toolLists):
        """
        Parses a list of tools (modules, functions, or classes/instances) to extract all public callable tools.
        Returns a dictionary of tool names to their callable objects.
        """
        tools = {}

        def addModuleFunctions(module):
            publicFunctions = {
                name: fn
                for name, fn in inspect.getmembers(module, inspect.isfunction)
                if not name.startswith("_")
            }
            tools.update(publicFunctions)

        def addClassMethods(module):
            for className, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ != module.__name__:
                    continue
                try:
                    instance = cls()
                except Exception:
                    instance = None
                for name, fn in inspect.getmembers(cls, inspect.isfunction):
                    if not name.startswith("_"):
                        funcKey = f"{className}.{name}"
                        tools[funcKey] = getattr(instance, name) if instance else fn

        for tool in toolLists:
            if inspect.ismodule(tool):
                addModuleFunctions(tool)
                addClassMethods(tool)
            elif inspect.isfunction(tool):
                if not tool.__name__.startswith("_"):
                    tools[tool.__name__] = tool
            elif inspect.isclass(tool):
                try:
                    instance = tool()
                except Exception:
                    instance = None
                className = tool.__name__
                for name, fn in inspect.getmembers(tool, inspect.isfunction):
                    if not name.startswith("_"):
                        funcKey = f"{className}.{name}"
                        tools[funcKey] = getattr(instance, name) if instance else fn
            elif hasattr(tool, "__class__"):
                # For instances passed directly
                className = tool.__class__.__name__
                for name, fn in inspect.getmembers(tool.__class__, inspect.isfunction):
                    if not name.startswith("_"):
                        funcKey = f"{className}.{name}"
                        tools[funcKey] = getattr(tool, name)

        return tools

    @staticmethod
    def extractJson(text):
        """
        Extract the first JSON array or object from a string, even if wrapped in markdown or extra commentary.
        """
        match = re.search(r"(\[.*?\]|\{.*?\})", text, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        return json.loads(text)

    @staticmethod
    def parseJsonSchema(func, schemaType):
        """
        Build a JSON schema for a function based on its signature and docstring metadata.
        schemaType can be 'completions', 'chat_completions', or 'responses'.
        Returns a dictionary representing the schema.
        """
        schemaType = schemaType.lower()
        if schemaType == "chat_completions":
            schemaType = "completions"
        sig = inspect.signature(func)
        typeHints = get_type_hints(func)
        properties = {}
        required = []
        TYPE_MAP = {int: "integer", float: "number", str: "string", bool: "boolean", dict: "object", list: "array"}

        for param in sig.parameters.values():
            paramType = typeHints.get(param.name, str)
            jsonType = TYPE_MAP.get(paramType, "string")
            properties[param.name] = {"type": jsonType}
            if param.default is param.empty:
                required.append(param.name)

        meta = ToolParser.parseToolDocstring(inspect.getdoc(func))
        descriptionLines = [meta["description"]]
        if meta.get("additional_information"):
            descriptionLines.append(f"Additional Information: {meta['additional_information']}")
        description = "\n".join(descriptionLines)

        schemaMap = {
            "completions": lambda: {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
            },
            "responses": lambda: {
                "type": "function",
                "name": func.__name__,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
        }

        return schemaMap[schemaType]()

    @staticmethod
    def parseTypedSchema(func):
        """
        Build a Google GenAI function declaration for a given function based on its signature and docstring metadata.
        Returns a FunctionDeclaration object.
        """
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        properties = {}
        type_map = {
            int: genai.types.Type.INTEGER,
            float: genai.types.Type.NUMBER,
            str: genai.types.Type.STRING,
            bool: genai.types.Type.BOOLEAN,
            dict: genai.types.Type.OBJECT,
            list: genai.types.Type.ARRAY,
        }
        for param in sig.parameters.values():
            param_type = type_hints.get(param.name, str)
            schema_type = type_map.get(param_type, genai.types.Type.STRING)
            properties[param.name] = genai.types.Schema(type=schema_type)

        meta = ToolParser.parseToolDocstring(inspect.getdoc(func))
        description_lines = [meta["description"]]
        if meta.get("additional_information"):
            description_lines.append(meta["additional_information"])
        # This is what will show up when you print it out
        description = "\n    ".join(description_lines)

        return types.FunctionDeclaration(
            name=func.__name__,
            description=description,
            parameters=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties=properties,
            ),
        )

    @staticmethod
    def addModuleFunctions(module, toolFunctions):
        """
        Adds all public standalone functions from a module to the toolFunctions dictionary.
        """
        publicFunctions = {
            name: fn
            for name, fn in inspect.getmembers(module, inspect.isfunction)
            if not name.startswith("_")
        }
        toolFunctions.update(publicFunctions)

    @staticmethod
    def addClassMethods(module, toolFunctions):
        """
        Adds all public methods from classes in a module to the toolFunctions dictionary.

        Each method is bound to an instance of the class to hide 'self' in the signature.
        """
        for className, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue
            try:
                instance = cls()
            except Exception:
                instance = None
            for name, fn in inspect.getmembers(cls, inspect.isfunction):
                if not name.startswith("_"):
                    funcKey = f"{className}.{name}"
                    toolFunctions[funcKey] = getattr(instance, name) if instance else fn
