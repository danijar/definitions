import os


def filename(relative):
    return os.path.join(os.path.dirname(__file__), relative)
