import os
import logging
from dotenv import load_dotenv
from SkillsManager import SkillsManager

load_dotenv()
logger = logging.getLogger(__name__)

skillsmanager = SkillsManager()
fooPath   = skillsmanager.getDir('Skills', 'Foo')
barPath   = skillsmanager.getDir('Skills', 'Bar')
toolsPath = skillsmanager.getDir('Tools')

fooSkills = []
barSkills = []
barTools  = []

printCapabilities = os.getenv('SHOW_CAPABILITIES', 'False') == 'True'
printMetaData     = os.getenv('SHOW_METADATA', 'False') == 'True'

# ----- Skills (Actions) -----
def loadSkills():
    skillsmanager.loadComponents(
        paths=[
            [fooPath],
            [barPath]
        ],
        components=[
            fooSkills,
            barSkills
        ],
        reloadable=[
            True,
            False
        ]
    )

def getFooActions(content):
    skills = (
            fooSkills
    )
    # return skillsmanager.getComponents(fooSkills, content)
    return skillsmanager.getComponents(skills, content)
    
def getBarActions():
    Skills = (
        barSkills
    )
    # return skillsmanager.getComponents(barSkills)
    return skillsmanager.getComponents(Skills)

def reloadSkills():
    original = getMetaData()
    skillsmanager.reloadSkills()
    new = getMetaData()
    for skill in new:
        if skill not in original:
            print(f"I've added the new skill {skill['className']} that {skill['description']}.\n")

def getMetaData():
    metaData = fooSkills + barSkills
    return skillsmanager.getMetaData(metaData, printMetaData)

def getCapabilities():
    return skillsmanager.getCapabilities(barSkills, printCapabilities)

def checkActions(action):
    return skillsmanager.checkActions(action)

def getActions(action):
    return skillsmanager.getActions(action)

def executeBarAction(actions, action):
    return skillsmanager.executeAction(actions, action)

def executeBarActions(actions, action):
    return skillsmanager.executeActions(actions, action)


# ----- Tools -----
def loadTools():
    skillsmanager.loadComponents(
        paths=[[toolsPath]],
        components=[barTools],
        reloadable=[False]
    )

def getTools():
    tools = (
        barTools
    )
    # return skillsmanager.getTools(barTools)
    return skillsmanager.getTools(tools)

def executeTool(name, tools, args, threshold=80, retry=True):
    return skillsmanager.executeTool(name, tools, args, threshold, retry)

def extractJson(text):
    return skillsmanager.extractJson(text)

def getJsonSchema(func, schemaType):
    return skillsmanager.getJsonSchema(func, schemaType)

def getTypedSchema(func):
    return skillsmanager.getTypedSchema(func)


# ----- Can be used with both skills and tools -----
def isStructured(*args):
    return skillsmanager.isStructured(*args)

def handleTypedFormat(role="user", content=""):
    return skillsmanager.handleTypedFormat(role, content)

def handleJsonFormat(role="user", content=""):
    return skillsmanager.handleJsonFormat(role, content)

def buildGoogleSafetySettings(harassment="BLOCK_NONE", hateSpeech="BLOCK_NONE", sexuallyExplicit="BLOCK_NONE", dangerousContent="BLOCK_NONE"):
    return skillsmanager.buildGoogleSafetySettings(harassment, hateSpeech, sexuallyExplicit, dangerousContent)
