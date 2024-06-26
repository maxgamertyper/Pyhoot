from setuptools import setup, find_packages

VERSION = '1.4.1'
DESCRIPTION = 'A Python library used for the Kahoot! Api'

with open("./README.md", 'r') as rm:
    Readme=rm.read()
    rm.close()
    
LONG_DESCRIPTION = Readme

setup(
    name="Pyhoot",
    version=VERSION,
    author="Maxgamertyper1 (Max Allen)",
    author_email="maxa5302@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=["requests", "beautifulsoup4", "websocket-client", "fake_useragent"],
    keywords=["Python", "Kahoot", "Pyhoot", "bot", "flooder", "Kahoot!","Library","Api","Kahoot api","Kahoot Python"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows"
    ],
    license="MIT",
    python_requires=">=3.6"
)
