
import inspect
import re
import logging
from inspect import Parameter
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class SkillParser:

    @staticmethod
    def fixPronouns(text: str) -> str:
        """
        Fix pronouns in the text to change perspective from first person to second person.
        This is useful for converting skill descriptions to be more user-centric.
        """
        text = re.sub(r'\bmyself\b', 'yourself', text, flags=re.IGNORECASE)
        text = re.sub(r'\bmy\b', 'your', text, flags=re.IGNORECASE)
        text = re.sub(r'\bme\b', 'you', text, flags=re.IGNORECASE)
        text = re.sub(r'\bi\b', 'you', text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def parseSkillDocstring(docstring: str) -> dict:
        """
        Parse a skill's docstring to extract description, additional information, and parameters.
        Returns a dictionary with keys 'description', 'additional', and 'params'.
        The 'params' key contains a dictionary of parameter names to their types and descriptions.
        If the docstring is empty or not provided, it returns a default structure with empty values.
        """
        parsed  = {"description": "", "additional": "", "params": {}}
        regex   = re.compile(r"(\*{0,2}\w+)\s*\((\w+)\)\s*:\s*(.*)")
        current = None
        in_desc = False

        for line in docstring.splitlines():
            s = line.strip()
            if s.startswith("Description:"):
                parsed["description"] = s.replace("Description:", "").strip()
                in_desc = True
                continue
            if s.startswith("Additional Information:"):
                parsed["additional"] = s.replace("Additional Information:", "").strip()
                continue
            if in_desc:
                if s and not s.startswith("Args:") and not s.startswith("Additional Information:"):
                    parsed["description"] += " " + s
                else:
                    in_desc = False
                continue
            if s.startswith("Args:"):
                continue
            m = regex.match(s)
            if m:
                name, ptype, desc = m.groups()
                parsed["params"][name] = {"type": ptype, "description": desc.strip()}
                current = name
            elif current and s:
                parsed["params"][current]["description"] += " " + s

        return parsed

    @staticmethod
    def formatAnnotation(annotation):
        """
        Format the annotation of a function parameter for display.
        If the annotation is empty, returns an empty string.
        If the annotation is a string, returns it directly.
        Otherwise, returns the name of the type.
        """
        if annotation is inspect.Parameter.empty:
            return ""
        if isinstance(annotation, str):
            return annotation
        return annotation.__name__

    @staticmethod
    def buildFunctionSignature(name, fn) -> str:
        """
        Build a string representation of a function's signature, excluding 'self' and formatting parameters.
        The signature will include parameter names and their types if available.
        If a parameter has a default value, it will be included in the signature.
        """
        sig = inspect.signature(fn)
        parts = []
        for p in sig.parameters.values():
            if p.name == "self":
                continue
            if p.kind == Parameter.VAR_POSITIONAL:
                pname = f"*{p.name}"
            elif p.kind == Parameter.VAR_KEYWORD:
                pname = f"**{p.name}"
            else:
                pname = p.name

            ann = SkillParser.formatAnnotation(p.annotation)
            parts.append(f"{pname}: {ann}" if ann else pname)

        return f"{name}({', '.join(parts)}):"

    @staticmethod
    def formatParamDetails(paramsDict: dict) -> str:
        """
        Format the parameters dictionary into a readable string representation.
        Each parameter will be displayed with its name, type, and description.
        If the parameter has no description, it will still show the name and type.
        """
        return "\n\n".join(
            f"Param: {k}\nParam Type: {v['type']}\nParam Description: {v['description']}"
            for k, v in paramsDict.items()
        )

    @staticmethod
    def formatCapabilityDoc(sig: str, desc: str, usage: dict, description: bool = False, showActions: bool = False, showParams: bool = False) -> str:
        """
        Format the capability documentation for a skill function.
        The documentation includes the function signature, description, and usage information.
        If `description` is True, it will include the description of the skill.
        If `showActions` is True, it will include action mappings if available.
        If `showParams` is True, it will include parameter details if available.
        """
        usage_section = ""
        if showActions and usage:
            lines = []
            for act, psets in usage.items():
                lines.append(f"- {act}:")
                if psets.get("required"):
                    lines.append(f"  Required: {', '.join(psets['required'])}")
                if psets.get("optional"):
                    lines.append(f"  Optional: {', '.join(psets['optional'])}")
            usage_section = "\nActions:\n" + "\n".join(lines)
        elif showParams and usage:
            lines = []
            if usage.get("required"):
                lines.append(f"  Required: {', '.join(usage['required'])}")
            if usage.get("optional"):
                lines.append(f"  Optional: {', '.join(usage['optional'])}")
            if lines:
                usage_section = "\n".join(lines)

        info = [f"{sig}"]
        if description and desc:
            info.append(f"\n{desc}")
        if usage_section:
            info.append(f"\n{usage_section.lstrip()}")
        return "\n".join(info).rstrip()

    @staticmethod
    def parseCapabilities(skills, description: bool = True) -> list:
        """
        Parse the capabilities of a list of skills, extracting function signatures, descriptions, and usage information.
        Each skill can be a module or a class with methods. The output is a list of formatted capability documentation strings.
        If `description` is True, it will include the description of the skill.
        If `skills` is empty, it returns an empty list.
        """
        capabilities = []

        for info in skills:
            try:
                is_module = inspect.ismodule(info)
                members   = inspect.getmembers(
                    info,
                    predicate=lambda m: inspect.ismethod(m) or inspect.isfunction(m)
                )
                action_maps = {}
                if isinstance(getattr(info, "actionMap", None), dict):
                    action_maps = info.actionMap
                elif isinstance(getattr(info, "ACTION_MAP", None), dict):
                    action_maps = info.ACTION_MAP

                for name, fn in members:
                    if name.startswith("_"):
                        continue

                    sig    = inspect.signature(fn)
                    params = sig.parameters.values()

                    is_dispatcher = (
                        "action" in sig.parameters and
                        any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
                    )

                    usage = {}
                    showActions = False
                    showParams = False

                    # dispatcher + ACTION_MAP
                    if is_dispatcher and action_maps:
                        showActions = True
                        for act, mapped in action_maps.items():
                            try:
                                mp_sig = inspect.signature(mapped)
                                req, opt = [], []
                                for p in mp_sig.parameters.values():
                                    if p.name == "self":
                                        continue
                                    text = p.name
                                    ann  = SkillParser.formatAnnotation(p.annotation)
                                    if p.default is inspect.Parameter.empty:
                                        if ann: text += f" ({ann})"
                                        req.append(text)
                                    else:
                                        if ann: text += f" ({ann})"
                                        opt.append(text)
                                usage[act] = {"required": req, "optional": opt}
                            except:
                                usage[act] = {"required": [], "optional": []}

                    # standalone module function
                    elif is_module:
                        req, opt = [], []
                        for p in params:
                            if p.name == "self":
                                continue
                            text = p.name
                            ann  = SkillParser.formatAnnotation(p.annotation)
                            if p.default is inspect.Parameter.empty:
                                if ann: text += f" ({ann})"
                                req.append(text)
                            else:
                                if ann: text += f" ({ann})"
                                opt.append(text)
                        if req or opt:
                            usage = {"required": req, "optional": opt}
                            showParams = True
                        else:
                            usage = {}

                    # build output
                    doc = inspect.getdoc(fn)
                    if doc:
                        parsed = SkillParser.parseSkillDocstring(doc)
                        desc = parsed.get("description", "")
                        additional = parsed.get("additional", "")
                        desc = f"Description: Allows you to {desc.lower()}" if desc else ""
                        if desc and additional:
                            desc = f"{desc}\nAdditional Information: {additional}"
                        elif additional:
                            desc = f"Additional information: {additional}"
                        sig_str = SkillParser.buildFunctionSignature(name, fn)
                        capabilities.append(
                            SkillParser.formatCapabilityDoc(sig_str, desc, usage, description, showActions, showParams)
                        )
                    else:
                        desc = ""
                        for metaAttr in ("_metaData", "_metadata"):
                            if hasattr(info, metaAttr) and callable(getattr(info, metaAttr)):
                                md_desc = getattr(info, metaAttr)().get("description", "")
                                if md_desc:
                                    desc = f"Description: Allows you to {SkillParser.fixPronouns(md_desc).lower()}"
                                    break

                        sig_str = SkillParser.buildFunctionSignature(name, fn)
                        capabilities.append(
                            SkillParser.formatCapabilityDoc(sig_str, desc, usage, description, showActions, showParams)
                        )

            except Exception as e:
                logger.error(f"SkillParser error: {e}", exc_info=True)

        return capabilities
