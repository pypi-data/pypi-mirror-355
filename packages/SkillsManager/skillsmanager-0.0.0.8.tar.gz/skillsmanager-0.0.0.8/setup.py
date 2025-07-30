# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name="SkillsManager",
    version="0.0.0.8",                         # bump to whatever's next
    packages=find_packages(where="SkillsManager"),
    package_dir={"": "SkillsManager"},
    include_package_data=True,
    install_requires=[
        "pyperclip",
        "pyautogui",
        "python-dotenv",
        "google-genai",
        "uv",
    ],
    author="Tristan McBride Sr.",
    author_email="TristanMcBrideSr@users.noreply.github.com",
    description="A modern way to auto load AI Skills/Tools",
)
