from setuptools import setup, find_packages

setup(
    name="ai-robot-position-finder",
    version="0.0.1",
    author="Arun CS",
    author_email="aruncs31s@proton.com",
    description="Python app to control the 16 Servo positions",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(where="src"),  
    package_dir={"": "src"}, 
    include_package_data=True,
    install_requires=[
        "requests",
        "click", 
    ],
    entry_points={
        "console_scripts": [
            "ai-ps=position_finder.position_finder:run",
        ]
    },
)