"""Sage helpers."""

__all__ = [
    "read_fraction",
]


import os.path
import re

import pandas as pd


def read_fraction(fpath: str) -> pd.DataFrame:
    """
    Read and reformat Sage output files.

    :param fpath: path to the Sage output directory.
    :return: DataFrame
    """
    search_file = os.path.join(fpath, "results.sage.tsv")
    tmt_file = os.path.join(fpath, "tmt.tsv")
    df_search = pd.read_table(search_file, index_col=["filename", "scannr"])
    df_tmt = pd.read_table(tmt_file, index_col=["filename", "scannr"])
    df_psm = pd.concat([df_search, df_tmt], axis=1, join="inner")
    df_psm.reset_index(inplace=True)

    mapping = {
        "proteins": "protein",
        "rt": "retention_time",
        "sage_discriminant_score": "PSM_score",
        "scannr": "spectrum",
        "spectrum_q": "PSM_q",
    }
    df_psm.rename(columns=mapping, inplace=True)

    df_psm["decoy"] = df_psm["label"].apply(lambda x: True if x == -1 else False)
    df_psm["decoy_training"] = False
    df_psm["decoy_testing"] = df_psm["decoy"]
    df_psm["file"] = fpath
    df_psm["modifications"] = df_psm["peptide"].apply(extract_modifications)
    df_psm["peptide"] = df_psm["peptide"].apply(strip_modifications)
    df_psm["protein"] = df_psm["protein"].apply(lambda x: x.split(";"))
    df_psm["PSM_score"] = - df_psm["PSM_score"] # less is better

    return df_psm


def strip_modifications(sequence: str) -> str:
    """
    Strip modifications from peptide sequence.

    :param sequence: peptide sequence with modifications.
    :return: peptide sequence.
    """
    res = re.findall(r"[A-Z]+", sequence)
    peptide = "".join(res)
    return peptide


def extract_modifications(sequence: str) -> dict:
    """
    Extract modifications from peptide sequence to dict
    {position: "mass"}.

    :param sequence: peptide sequence with modifications.
    :return: dict of modifications.
    """
    pattern = r"\[(\+\d+\.\d+)\]\-?"
    remainder = sequence
    modifications = {}
    position = 0
    while True:
        match = re.search(pattern, remainder)
        if match:
            position += match.start()
            modifications[position] = match.group(1)
            remainder = remainder[match.end() :]
        else:
            break
    return modifications
