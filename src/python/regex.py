import re

REGEX_FIX_SLASHES = re.compile(r'[\\/]+')
REGEX_SPLIT_CAMEL_CASE = re.compile(r'_|\W+|\s+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9]+)|(?<=[0-9])(?=[a-zA-Z]+)')
REGEX_NORM_ECLIPSE = re.compile(r"L([^;]+);.*") #todo: why is this called eclipse?
REGEX_PROJECT = re.compile(r"\/(.*)\/src/.*")


#todo: move language specific regex to appropriate processors
#JS specific
REGEX_NORM_JS_PATH = re.compile(r"(.*)\.js")
REGEX_JS_PROJECT = re.compile(r"(.*?)\/")

#Java specific
REGEX_NORM_JAVA_PATH = re.compile(r".*src\/(.*)\.java")
REGEX_JAVA_PACKAGE = re.compile(r"(.*)/[a-zA-Z0-9]+")


def fixSlashes(s):
    # Replaces '\' with '/'
    return REGEX_FIX_SLASHES.sub('/', s)
