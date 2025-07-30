from main import main

with open("version.txt", "r") as raw_file:
    file = raw_file.readline()
__version__ = file


print(__version__)