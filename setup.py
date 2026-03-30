"""
Agency Research Automation — Package Setup
Owner: Md Jamil Islam
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agency-research-automation",
    version="1.0.0",
    author="Md Jamil Islam",
    author_email="agency@example.com",
    description="Automated agency client research and outreach system targeting $1M revenue",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Joy123123123/agency-research-automation-1m",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "agency-research=scripts.run_research:main",
            "agency-outreach=scripts.send_outreach:main",
            "agency-report=scripts.generate_report:main",
        ],
    },
)
