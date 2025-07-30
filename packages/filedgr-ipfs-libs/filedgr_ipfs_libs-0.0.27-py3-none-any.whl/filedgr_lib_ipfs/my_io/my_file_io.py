import os


def build_dir_tree(path: str, recursive: bool = True):
    if not os.path.exists(path) and not os.path.isdir(path):
        raise NotADirectoryError(f"The provided path [{path}] does not lead to a directory.")
    listOfFiles = list()
    listOfDirs = [path]
    for (dirpath, dirnames, filenames) in os.walk(path):
        listOfDirs += [os.path.join(dirpath, dir) for dir in dirnames]
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]
    return listOfDirs, listOfFiles