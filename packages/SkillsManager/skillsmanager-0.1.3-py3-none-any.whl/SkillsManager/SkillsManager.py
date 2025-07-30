

import inspect
import threading
import logging
from pathlib import Path

from .SMLoader.Loader import Loader
from .SMParsers.ArgumentParser.ArgumentParser import ArgumentParser
from .SMParsers.ActionParser.ActionParser import ActionParser
from .SMParsers.SkillParser.SkillParser import SkillParser
from .SMParsers.ToolParser.ToolParser import ToolParser
from .SMPackageManager.PackageManager import PackageManager
from .SMUtils.Utils import *

logger = logging.getLogger(__name__)


class SkillsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SkillsManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, autoReload=False, cycleInterval=60):
        if getattr(self, 'initialized', False):
            return
        self._initComponents(autoReload, cycleInterval)
        self.initialized = True

    def _initComponents(self, autoReload, cycleInterval):
        self.loader               = Loader()
        self.actionParser         = ActionParser()
        self.autoReload           = autoReload
        self.cycleInterval        = cycleInterval
        self.timer                = None
        self.reloadableComponents = []
        if self.autoReload:
            self.reloadTimer()

    def getDir(self, *paths):
        """
        Returns the absolute path of the given paths.
        """
        return str(Path(*paths).resolve())

    def setAutoReload(self, autoReload: bool = False, cycleInterval: int = 60) -> None:
        """
        Set whether to automatically reload skills after a certain interval.
        If autoReload is True, starts the timer for reloading skills.
        If False, stops the timer if it is running.
        """
        self.cycleInterval = cycleInterval
        self.autoReload = autoReload
        if self.autoReload:
            self.reloadTimer()
        elif self.timer:
            self.timer.cancel()
            self.timer = None

    def setEnvDir(self, envDir: str = None) -> None:
        """
        Set the directory for the virtual environment.
        This is used to load skills from a specific environment.
        """
        PackageManager().setEnvDir(envDir)

    def loadComponents(self, paths: list = None, components: list = None, reloadable: list = None):
        """
        Load multiple component groups by passing parallel lists:
        - paths:       list of path lists
        - components:  list of component lists
        - reloadable:  list of bools (optional, defaults to all False)
        """
        if not paths or not components:
            raise ValueError("Both 'paths' and 'components' are required.")
        if len(paths) != len(components):
            raise ValueError("'paths' and 'components' must be the same length.")
        reloadable = reloadable or [False] * len(paths)
        if len(reloadable) != len(paths):
            raise ValueError("'reloadable' must be the same length as 'paths' and 'components'.")

        for p, c, r in zip(paths, components, reloadable):
            for path in p or []:
                self.loadSkills(path, c)
            if r and (c, p) not in self.reloadableComponents:
                self.reloadableComponents.append((c, p))

    def loadSkills(self, source, component = None):
        return self.loader.loadSkills(source, component)

    def reloadTimer(self):
        """
        Starts or restarts the timer for auto-reloading skills.
        If a timer is already running, it cancels it first.
        """
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.cycleInterval, self.reloadSkills)
        self.timer.start()

    def reloadSkills(self):
        """
        Reload all registered reloadable skill components,
        update metadata, and restart the timer.
        """
        if not self.reloadableComponents:
            return
        # Reload all registered reloadable skill components
        if self.reloadableComponents:
            for component, paths in self.reloadableComponents:
                component.clear()
                for path in paths or []:
                    self.loadSkills(path, component)

        if self.autoReload:
            self.reloadTimer()

    def getComponents(self, skills, content= None):
        """
        Returns actions or executes an action depending on the arguments.
        - If content is provided, executes actions on the skills with that content.
        - If content is None, returns a dict of all available actions.
        """
        if content is not None:
            return self.getUserActions(skills, content)
        return self.getSelfActions(skills)

    def getUserActions(self, skills, content):
        """
        Runs executeAction(content) on the first skill that returns a result.
        'skills' must be a list of skill objects to check.
        """
        # Flatten skills in case someone passes a list of lists/tuples
        flat_skills = []
        for group in skills:
            if isinstance(group, (list, tuple)):
                flat_skills.extend(group)
            else:
                flat_skills.append(group)
        for executor in flat_skills:
            action = executor.executeAction(content)
            if action is not None:
                return action
        return None

    def getSelfActions(self, skills):
        """
        Returns a dict of action methods from the given skill(s).
        Accepts a single skill instance or a list/tuple of skills.
        """
        if not isinstance(skills, (list, tuple)):
            skills = [skills]

        graph = {}
        for skill in skills:
            for name, method in inspect.getmembers(
                skill,
                predicate=lambda m: inspect.ismethod(m) or inspect.isfunction(m)
            ):
                if name.startswith("_"):
                    continue
                graph[name] = method
        return graph

    def getMetaData(self, skillGroups=None, printMetaData=False):
        """
        Returns a list of metadata dictionaries for the given skill groups.
        If skillGroups is None, defaults to all skills ending with 'Skills' in the class.
        If printMetaData is True, prints the metadata to the console.
        """
        if skillGroups is None:
            skillGroups = [
                getattr(self, name) for name in dir(self)
                if name.endswith('Skills') and isinstance(getattr(self, name), list)
            ]
        # Flatten if list of lists
        if isinstance(skillGroups, (list, tuple)):
            skills = []
            for group in skillGroups:
                if isinstance(group, (list, tuple)):
                    skills.extend(group)
                else:
                    skills.append(group)
        else:
            skills = [skillGroups]

        metaList = []
        for comp in skills:
            # Try both _metaData and _metadata (case-insensitive)
            metaMethod = next(
                (getattr(comp, methodName) for methodName in ['_metaData', '_metadata']
                 if hasattr(comp, methodName) and callable(getattr(comp, methodName))),
                None
            )
            if metaMethod:
                md = metaMethod()
                metaList.append({
                    "className": md.get("className", "Unknown"),
                    "description": f"Allows me to {md.get('description','').lower()}"
                })

        if printMetaData:
            self.printMetaDataInfo(metaList)
        return metaList

    def parseCapabilities(self, skills, description = True):
        """
        Parses the capabilities of the given skills and returns a list of capabilities.
        If skills is a single skill, it will be wrapped in a list.
        If description is True, it get information about the capabilities from the docstring.
        """
        return SkillParser.parseCapabilities(skills, description)

    def checkActions(self, action: str) -> str:
        """
        Checks if the given action string matches any of the available actions.
        If the action string is empty, it returns a message indicating that no action was provided.
        If the action string matches an available action, it returns the action string.
        If the action string does not match any available actions, it returns None.
        """
        return self.actionParser.checkActions(action)

    def getActions(self, action: str) -> list:
        """
        Returns a list of actions that match the given action string.
        If the action string is empty, it returns all available actions.
        """
        return self.actionParser.getActions(action)

    def executeAction(self, actions, action):
        """
        Executes a single action from the list of actions.
        If the action is not found, it returns None.
        """
        return self.actionParser.executeAction(actions, action)

    def executeActions(self, actions, action):
        """
        Executes a single action or multiple actions from the list of actions.
        It will execute each action in the list in a for loop, if the action is a list.
        If the action is not found, it returns None.
        """
        return self.actionParser.executeActions(actions, action)

    def getCapabilities(self, skillList: list, printCapabilities = False, description = False):
        """
        Returns a human-readable list of capabilities for the given skill(s).
        If skillList is a single skill, it will be wrapped in a list.
        If printCapabilities is True, it will print the capabilities to the console.
        If description is True, it will include a human-readable description.
        """
        skills = skillList if isinstance(skillList, list) else [skillList]
        caps = self.parseCapabilities(skills, description)
        if printCapabilities:
            self.printCapabilitiesInfo(caps)
        return "\n\n".join(caps)

    def printCapabilitiesInfo(self, graph):
        print("Human-readable Format:")
        for item in graph:
            print("\n=== Capability ===\n")
            print(item)
            print("\n" + "=" * 50 + "\n")

        print("My-readable Format:")
        print(graph)

    def printMetaDataInfo(self, metaList):
        print("Human-readable Format:")
        for m in metaList:
            print(f"\n=== MetaData ===\n")
            print(f"Class: {m['className']} | Description: {m['description']}")
            print("\n" + "=" * 50 + "\n")

        print("My-readable Format:")
        print(metaList)

    def actionInstructions(self, capabilities):
        return (
            f"You are the action process you determine the best course of action. "
            f"Select the most logical action or actions from the list:\n{capabilities}. \n\n"
            "If more than one action is required, they should be listed in the exact order of execution, separated by commas. "
            "For actions requiring context or content, use what user said. "
            "If no action is necessary, respond only with 'None'. "
            "Respond only with the exact action name(s) or 'None'. No extra text or explanation is allowed.\n\n"

            "Examples:\n"
            "- ['get_current_date()']\n"
            "- ['get_current_time()']\n"
            "- ['get_current_date()','get_current_time()']\n"
            "- ['get_temperature(\"latitude\", \"longitude\")']\n"
            "- ['get_humidity(\"latitude\", \"longitude\")']\n"
            "- ['get_wind_speed(\"latitude\", \"longitude\")']\n"
            "- ['appAction(\"open\", \"Notepad\")']\n"
            "- ['appAction(\"open\", \"Notepad\")','appAction(\"open\", \"Word\")']\n"
            "- If no action is needed, respond with: None\n"
        )
    


    # Can be used with both skills and tools
    def isStructured(self, *args):
        """
        Check if any of the arguments is a list of dictionaries.
        This indicates structured input (multi-message format).
        """
        return isStructured(*args)

    def handleTypedFormat(self, role: str = "user", content: str = ""):
        """
        Format content for Google GenAI APIs.
        """
        return handleTypedFormat(role, content)

    def handleJsonFormat(self, role: str = "user", content: str = ""):
        """
        Format content for OpenAI APIs and similar JSON-based APIs.
        """
        return handleJsonFormat(role, content)

    def formatTypedExamples(self, items):
        """
        Handle roles for Google GenAI APIs, converting items to Gemini Content/Part types.
        Accepts a list of (role, value) tuples, where value can be:
            - str: will be wrapped using handleTypedFormat
            - dict: wrapped as Content with role, value as text
            - list of dicts: each dict converted to Content with role, dict as text
        Returns a flat list of Content objects.
        """
        return formatTypedExamples(items)

    def formatJsonExamples(self, items):
        """
        Handle roles for OpenAI APIs, converting items to JSON message format.
        Accepts a list of (role, value) tuples, where value can be:
            - str: will be wrapped using handleJsonFormat
            - dict: added as-is
            - list of dicts: each dict is added individually
        Returns a flat list of message dicts.
        """
        return formatJsonExamples(items)

    def formatExamples(self, items, formatFunc):
        """
        Ultra-robust handler for formatting few-shot or behavioral examples.
        Accepts any mix of (role, value) pairs—strings, dicts, numbers, bools, lists, and any nested structure.
        Silently ignores None. Converts numbers and bools to strings.
        """
        return formatExamples(items, formatFunc)

    def handleTypedExamples(self, items):
        """
        Handle roles for Google GenAI APIs, converting items to Gemini Content/Part types.
        Accepts a list of (role, value) tuples, where value can be:
            - str: will be wrapped using handleTypedFormat
            - dict: wrapped as Content with role, value as text
            - list of dicts: each dict converted to Content with role, dict as text
        Returns a flat list of Content objects.
        """
        return handleTypedExamples(items)

    def handleJsonExamples(self, items):
        """
        Handle roles for OpenAI APIs, converting items to JSON message format.
        Accepts a list of (role, value) tuples, where value can be:
            - str: will be wrapped using handleJsonFormat
            - dict: added as-is
            - list of dicts: each dict is added individually
        Returns a flat list of message dicts.
        """
        return handleJsonExamples(items)

    def handleExamples(self, items, formatFunc):
        """
        Ultra-robust handler for formatting few-shot or behavioral examples.
        Accepts any mix of (role, value) pairs—strings, dicts, numbers, bools, lists, and any nested structure.
        Silently ignores None. Converts numbers and bools to strings.
        """
        return handleExamples(items, formatFunc)
        

    def buildGoogleSafetySettings(self, harassment="BLOCK_NONE", hateSpeech="BLOCK_NONE", sexuallyExplicit="BLOCK_NONE", dangerousContent="BLOCK_NONE"):
        """
        Construct a list of Google GenAI SafetySetting objects.
        """
        return buildGoogleSafetySettings(harassment, hateSpeech, sexuallyExplicit, dangerousContent)



    # Everything below this point is related to tools
    def getTools(self, toolList: list):
        """
        Parses a list of tools (modules, functions, or classes) to extract callable tools.
        Returns a dictionary of tool names to their callable objects.
        If a skill is a module, it extracts all functions defined in that module.
        """
        return ToolParser.getTools(toolList)

    def parseTools(self, docstring):
        """
        Parses a docstring to extract tool metadata, including name, description, and parameters.
        """
        return ToolParser.parseToolDocstring(docstring)

    def extractJson(self, text):
        """
        Extract the first JSON array or object from a string, even if wrapped in markdown or extra commentary.
        """
        return ToolParser.extractJson(text)

    def getTypedSchema(self, func):
        """
        Build a Google GenAI function declaration for a given function based on its signature and docstring metadata.
        Returns a FunctionDeclaration object.
        """
        return ToolParser.parseTypedSchema(func)

    def getJsonSchema(self, func, schemaType):
        """
        Build a JSON schema for a function based on its signature and docstring metadata.
        The schemaType can be either 'completions' or 'responses'.
        Returns a dictionary representing the schema.
        """
        return ToolParser.parseJsonSchema(func, schemaType)

    def executeTool(self, name, tools, args, threshold=80, retry=False):
        """
        Call a tool by its name, auto-fixing missing argument names using fuzzy matching if needed.
        - threshold: Minimum match score for fuzzy correction.
        - retry: Whether to retry the tool call with corrected args.
        """
        return self.actionParser.executeTool(name, tools, args, threshold, retry)
