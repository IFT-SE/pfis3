import re

REGEX_FIX_SLASHES = re.compile(r'[\\/]+')
REGEX_SPLIT_CAMEL_CASE = re.compile(r'_|\W+|\s+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9]+)|(?<=[0-9])(?=[a-zA-Z]+)')
REGEX_NORM_ECLIPSE = re.compile(r"L([^;]+);.*") #todo: why is this called eclipse?
REGEX_NORM_JAVA_PATH = re.compile(r".*src\/(.*)\.java")
REGEX_PROJECT = re.compile(r"\/(.*)\/src/.*")
REGEX_PACKAGE = re.compile(r"(.*)/[a-zA-Z0-9]+")

def fixSlashes(s):
    # Replaces '\' with '/'
    return REGEX_FIX_SLASHES.sub('/', s)
