
import os
import logging
import threading
from dotenv import load_dotenv
from SkillsManager import SkillsManager

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ClassName: # This is a placeholder for the class name, replace with your actual class name
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ClassName, cls).__new__(cls) # Remember to replace ClassName with your actual class name
        return cls._instance

    def __init__(self):
        if getattr(self, 'initialized', False):
            return
        self.skillsmanager = SkillsManager()
        self.fooPath   = self.getDir('Skills', 'Foo')
        self.barPath   = self.getDir('Skills', 'Bar')
        self.toolsPath = self.getDir('Tools')
        self.fooSkills = []
        self.barSkills = []
        self.barTools  = []
        self.printCapabilities = os.getenv('SHOW_CAPABILITIES', 'False') == 'True'
        self.printMetaData     = os.getenv('SHOW_METADATA', 'False') == 'True'
        self.loadSkills()
        self.loadTools()
        self.initialized = True

    def getDir(self, *paths):
        return self.skillsmanager.getDir(*paths)

    # ----- Skills (Actions) -----
    def loadSkills(self):
        self.skillsmanager.loadComponents(
            paths=[
                [self.fooPath],
                [self.barPath]
            ],
            components=[
                self.fooSkills,
                self.barSkills
            ],
            reloadable=[
                True,
                False
            ]
        )

    def getFooActions(self, content):
        skills = (
            self.fooSkills
        )
        # return self.skillsmanager.getComponents(self.fooSkills, content)
        return self.skillsmanager.getComponents(skills, content)

    def getBarActions(self):
        skills = (
            self.barSkills
        )
        # return self.skillsmanager.getComponents(self.barSkills)
        return self.skillsmanager.getComponents(skills)

    def reloadSkills(self):
        original = self.getMetaData()
        self.skillsmanager.reloadSkills()
        new = self.getMetaData()
        for skill in new:
            if skill not in original:
                print(f"I've added the new skill {skill['className']} that {skill['description']}.\n")

    def getMetaData(self):
        metaData = (
            self.fooSkills + self.barSkills
        )
        return self.skillsmanager.getMetaData(metaData, self.printMetaData)

    def getCapabilities(self):
        return self.skillsmanager.getCapabilities(self.barSkills, self.printCapabilities)

    def checkActions(self, action: str):
        return self.skillsmanager.checkActions(action)

    def getActions(self, action: str):
        return self.skillsmanager.getActions(action)

    def executeBarAction(self, actions, action):
        return self.skillsmanager.executeAction(actions, action)

    def executeBarActions(self, actions, action):
        return self.skillsmanager.executeActions(actions, action)


    # ----- Tools -----
    def loadTools(self):
        self.skillsmanager.loadComponents(
            paths=[[self.toolsPath]],
            components=[self.barTools],
            reloadable=[False]
        )

    def getTools(self):
        tools = (
            self.barTools
        )
        # return self.skillsmanager.getTools(self.barTools)
        return self.skillsmanager.getTools(tools)

    def executeTool(self, name, tools, args, threshold=80, retry=True):
        return self.skillsmanager.executeTool(name, tools, args, threshold, retry)

    def extractJson(self, text):
        return self.skillsmanager.extractJson(text)

    def getJsonSchema(self, func, schemaType):
        return self.skillsmanager.getJsonSchema(func, schemaType)

    def getTypedSchema(self, func):
        return self.skillsmanager.getTypedSchema(func)


    # ----- Can be used with both skills and tools -----
    def isStructured(self, *args):
        return self.skillsmanager.isStructured(*args)

    def handleTypedFormat(self, role: str = "user", content: str = ""):
        return self.skillsmanager.handleTypedFormat(role, content)


    def handleJsonFormat(self, role: str = "user", content: str = ""):
        return self.skillsmanager.handleJsonFormat(role, content)

    def buildGoogleSafetySettings(self, harassment="BLOCK_NONE", hateSpeech="BLOCK_NONE", sexuallyExplicit="BLOCK_NONE", dangerousContent="BLOCK_NONE"):
        return self.skillsmanager.buildGoogleSafetySettings(harassment, hateSpeech, sexuallyExplicit, dangerousContent)