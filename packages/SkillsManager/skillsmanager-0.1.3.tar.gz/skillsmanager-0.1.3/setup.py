# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name="SkillsManager",
    version="0.1.3",
    packages=find_packages(),
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
