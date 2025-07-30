from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="society_pc_control",
    version="0.1.0",
    author="fzcociety",
    author_email="userexamplehx@gmail.com",
    description="Телеграм бот и библиотека для удаленного управления ПК (мышь, клавиатура)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyTelegramBotAPI",
        "pyautogui",
        "pillow",
        "opencv-python",
        "numpy",
        "python-dotenv" 
    ],
)
