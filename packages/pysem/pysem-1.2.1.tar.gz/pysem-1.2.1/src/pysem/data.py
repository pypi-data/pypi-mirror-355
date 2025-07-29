from pathlib import Path
import csv
import zipfile
import json
import codecs


def data_path(*path):
    return Path(__file__).parent.joinpath("data", *path)


with codecs.open(data_path("sense.csv"), "r", "utf-8") as f:
    SENSE = {}
    for row in csv.DictReader(f, delimiter=","):
        SENSE[row["HEADWORD"]] = frozenset(row["ITEMS"].split(";")[:-1])


def get_Concepticon():
    with zipfile.ZipFile(data_path("concepticon.zip").as_posix(), "r") as zf:
        concepticon = json.loads(zf.read("concepticon.json"))
    return concepticon
