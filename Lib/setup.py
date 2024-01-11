from setuptools import setup, find_packages

VERSION = '1.2.1'
DESCRIPTION = 'A Python library used for the Kahoot! Api'
LONG_DESCRIPTION = 'A package that allows users to create Kahoot! clients and use the Kahoot! API to their will.\nCheck out https://github.com/maxgamertyper/Pyhoot for more information.'


setup(
    name="Pyhoot",
    version=VERSION,
    author="Maxgamertyper1 (Max Allen)",
    author_email="maxa5302@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['requests', 'beautifulsoup4', 'websocket-client', 'fake_useragent'],
    keywords=['python', 'Kahoot', 'pyhoot', 'bot', 'flooder', 'sockets'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows"
    ],
    license="MIT",
    python_requires=">=3.6"
)
