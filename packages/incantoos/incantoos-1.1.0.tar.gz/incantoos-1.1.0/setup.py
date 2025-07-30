import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup_info = {
    "name": "incantoos",
    "version": "1.1.0",
    "author": "NinoTheMeano",
    "author_email": "ninosdeveloping@gmail.com",
    "description": "IncantoOS Is a wrapper related to OS functions that can be put into a smaller faster function",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "url": "https://github.com/NinoTheMeano/incantoos",
    "packages": setuptools.find_packages(),
    "classifiers": [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: AsyncIO",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
        "Topic :: Software Development :: Libraries"
    ],
    "project_urls": {
        "Discord": "https://discord.com/users/255125932447236096"
    },
    "python_requires": '>=3.8',
    "install_requires": []
}


setuptools.setup(**setup_info)