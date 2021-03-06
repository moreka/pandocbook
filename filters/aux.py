import yaml
import os
import re
import sys


def loadyaml(file):
    """Utility function to load from yaml file"""
    try:
        with open(file, "r", encoding="utf-8") as f:
            t = yaml.load(f, Loader=yaml.FullLoader)
            return t
    except FileNotFoundError:
        return dict()


def dumpyaml(obj, file):
    """Utility function to write object to yaml file"""
    with open(file, "w", encoding="utf-8") as f:
        yaml.dump(obj, f)


def _readaux(f, path="."):
    """
    Read the aux file f and return dictionary dic with
    dic[label] = {"file":filename (no ext), "class": type (section, theorem, etc..) , "number": number of object (e.g., 1.3)}
    for sections
    TOC[number] = {"filename": file, "title": title, "href": labelid}
    """

    onlyfile = os.path.splitext(f)[0]
    fullname = os.path.join(path, f)
    reg = re.compile(r'\\newlabel\{([a-zA-Z\-\_0-9\:]+)\@pref\}'
                     + r'\{\{\[([a-zA-Z ]+)\]\[([a-zA-Z0-9 ]*)\]'
                     + r'\[([a-zA-Z0-9\,\. ]*)\]([a-zA-Z0-9\,\. ]*)\}.*\}')

    d = dict()
    with open(fullname, "r",encoding="utf-8") as aux:
        lines = aux.read().split("\n")
        for l in lines:
            m = reg.match(l)
            if m:
                label, kind , _ , _ , number = m.groups()
                d[label] = {"file":onlyfile,"class":kind,"number": number}
    return d

def readallaux(path):
    """
    Read all aux files in a directory into a dictionary
    """
    D = {}
    auxfiles = [f for f in os.listdir(path) 
            if os.path.isfile(os.path.join(path, f)) and len(f) > 4 and f[-4:] == ".aux"]

    for f in auxfiles:
        D.update(_readaux(f,path))

    return D

def dumpdict(dic, filename):
    """Utility function to dump a dictoinary to a yaml file"""

    with open(filename,mode="w", encoding="utf-8") as file:
        yaml.dump(dic, file)


def main():
    args = sys.argv[1:]
    path = args[0] if args else "."
    file = args[1] if len(args) > 1 else "bookaux.yaml"
    D = readallaux(path)
    dumpdict(D,file)


if __name__ == "__main__":
    main()

