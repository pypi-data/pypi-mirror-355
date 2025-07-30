from setuptools import setup, find_packages

setup(
    name="SkillsManager",
    version="0.0.0.2",
    packages=find_packages(where="SkillsManager"),
    package_dir={"": "SkillsManager"},
    install_requires=[
        "pyperclip",
        "pyautogui",
        "python-dotenv",
        "google-genai",
        "uv",
    ],
    author="Tristan McBride Sr.",
    author_email="142635792+TristanMcBrideSr@users.noreply.github.com",
    description="A modern way to auto load AI Skills/Tools",
)

