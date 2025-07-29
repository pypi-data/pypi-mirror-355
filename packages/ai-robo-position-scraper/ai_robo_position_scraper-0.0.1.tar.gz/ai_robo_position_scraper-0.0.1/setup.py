from setuptools import setup, find_packages

setup(
    name="ai_robo_position_scraper",
    version="0.0.1",
    author="Arun CS",
    author_email="your.email@example.com",
    description="Position scraper library for AI-Robot",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aruncs31s/ai_robo_position_scraper",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=["requests"],
)
