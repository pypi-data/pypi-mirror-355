"""Miscellaneous functions."""

__all__ = [
    "protein_abundance",
    "drop_decoys_from_protein_group",
    "get_gene_name",
    "load_gene_mapping",
    "groupwise_qvalues",
    "indicator",
    "mods_read_from_settings",
    "mods_convert_mass_to_label",
    "apply_modifications",
    "weighted_mean",
    "mean_and_std",
    "uniq",
]


import logging
import re
from collections.abc import Iterable
from typing import Callable, Union

import numpy as np

try:
    from astropy.stats import biweight_scale, median_absolute_deviation
except ModuleNotFoundError:
    from .astropy_stats import biweight_scale, median_absolute_deviation

import pandas as pd
from pyteomics import auxiliary as paux

from .altsp import GeneralPsmGroup

logger = logging.getLogger(__name__)


def uniq(x: Iterable[str], sort=True) -> list:
    """
    Filter out repeated elements from the input list.

    :param x: Iterable.
    :param sort: If True, return sorted list.
    :return: List of unique elements.
    """
    y = list(set(x))
    y = sorted(y) if sort else y
    return y


def get_gene_name(protein_descr: str, missing_gene: str = "_not_found") -> str:
    """
    Parse protein description for gene name. Supported fasta format:
    UniProt/Swiss-Prot, Ensembl.

    :param protein_descr: Protein description from FASTA header.
    :param missing_gene: String to return if gene name is not found.
    :return: Gene name.
    """
    pattern = r"(GN=|gene_symbol:)(\S*)"
    res = re.search(pattern, protein_descr)
    if res:
        return res.group(2)
    return missing_gene


def load_gene_mapping(fpath: str) -> dict:
    """
    Read protein fasta and return {"protein id": "gene_name"} dict.

    :param fpath: path to fasta file.
    :return: dict of {protein: gene}.
    """
    mapping = {}
    missing_gene = "_not_found"
    with open(fpath, "rt") as f:
        for line in f:
            if line[0] == ">":
                res = line[1:].rstrip().split(sep=" ", maxsplit=1)
                protein = res[0]
                descr = res[1] if len(res) > 1 else ""
                gene = get_gene_name(descr, missing_gene)
                mapping[protein] = gene
    genes = uniq(mapping.values())
    total = len(genes)
    if len(genes) == 0 or len(genes) == 1 and genes[0] == "_not_found":
        logger.warning("No gene info in protein fasta headers.")
    else:
        logger.info(f"Total gene names found in protein fasta headers: {total}")
    return mapping


def drop_decoys_from_protein_group(protein_group: list, decoy_prefix: str = "DECOY_"):
    """
    Drop decoy proteins from protein group and sort remaining proteins.

    :param protein_group: list of proteins
    :param decoy_prefix: Decoy prefix, defaults to 'DECOY_'.
    :return: sorted list of proteins
    """
    # work around Identipy erroneously reporting duplicates in protein group
    # return sorted([p for p in protein_group if not p.startswith(decoy_prefix)])
    return uniq([p for p in protein_group if not p.startswith(decoy_prefix)])


def groupwise_qvalues(
    df_psm: pd.DataFrame,
    psm_group: GeneralPsmGroup,
    training: str = "decoy_training",
    testing: str = "decoy_testing",
    score: str = "PSM_score",
) -> pd.DataFrame:
    """
    Calculate groupwise qvalues for `psm_group` in `df_psm`. Return new DataFrame with
    group PSMs and q-values stored in `group_q` column.

    :param df_psm: Scavager PSMs_full DataFrame.
    :param psm_group: PSMs group to calculate qvalues.
    :param training: column name for training decoys.
    :param testing: column name for testing decoys.
    :param score: column name for PSM score.
    :return: DataFrame with group PSMs.
    """

    group_ind = psm_group.target_ind | psm_group.decoy_ind
    df_group = df_psm[group_ind]

    group_pep_ratio = df_group[testing].sum() / df_group["decoy"].sum()
    # filter out decoy which were used for CatBoost training
    df_group = df_group[~df_group[training]].copy()

    res = paux.qvalues(
        df_group,
        key=score,
        is_decoy=testing,
        remove_decoy=False,
        ratio=group_pep_ratio,
        formula=1,
        full_output=True,
        correction=1,
    )
    df_group["group_q"] = res["q"]
    return df_group


def indicator(
    df: pd.DataFrame, cols: list[str], ind_func: Callable[[float], bool] = bool
) -> pd.Series:
    """
    Return boolean array for indexing rows where `ind_func` is True for all columns in
    the DataFrame.

    :param df: DataFrame.
    :param cols: List of columns.
    :param ind_func: Boolean function.
    :return: Boolean array.
    """
    return df[cols].map(ind_func).all(axis="columns")


def mods_read_from_settings(modifications: dict) -> dict:
    """
    Convert modifications from TMTCrunch settings to a dict of mass and label pairs.

    :param modifications: dict of modifications from TMTCrunch settings.
    :return: tuple of dict for all mods and dict for selective mods.
    """
    return {mod["mass"]: mod["modX"] for mod in modifications.values()}


def mods_convert_mass_to_label(
    modifications: dict, label_for_mass: dict, unrecognized: bool = True
) -> dict | tuple[dict, dict]:
    """
    Convert modifications from {position: "mass"} to {position: "label"} format using
    dict of {"mass": "label"} and return converted modifications and optionally
    unrecognized modifications.

    :param modifications: dict of modifications {position: "mass"}.
    :param label_for_mass: dict of {"mass": "label"}.
    :param unrecognized: If True, return also a dict of unrecognized modifications.
    :return: dict of modifications or tuple of dict of modifications and dict of
        unrecognized modifications.
    """
    recognized_mods = {
        i: label_for_mass[mass]
        for i, mass in modifications.items()
        if mass in label_for_mass.keys()
    }
    if unrecognized:
        unknown_mods_loc = list(modifications.keys() - recognized_mods.keys())
        unknown_mods = {i: modifications[i] for i in unknown_mods_loc}
        return recognized_mods, unknown_mods
    else:
        return recognized_mods


def apply_modifications(sequence: str, modifications: dict) -> str:
    """
    Apply modifications for amino- sequence and return modified sequence.

    :param sequence: Original peptide sequence.
    :param modifications: dict of modifications {location: "label"}.
    :return: Modified peptide sequence.
    """
    if len(modifications) == 0:
        return sequence

    modified = ""
    # Note: First aminoacid in a sequence has location 1.
    # Modification at zero location is prepended to the sequence.
    mod_loc = sorted(modifications.keys())

    # Prepend n-term modification.
    if mod_loc[0] == 0:
        modified = modifications[0]
        if len(mod_loc) == 1:  # n-term was the only modification.
            modified += sequence
            return modified
        else:
            mod_loc = mod_loc[1:]

    # Transform sequence.
    for i_l, i_r in zip([0] + mod_loc[:-1], mod_loc):
        modified += sequence[i_l : i_r - 1] + modifications[i_r]
    # Append sequence tail.
    modified += sequence[mod_loc[-1] :]

    return modified


def weighted_mean(
    data: np.array,
    data_err: np.array = None,
    axis: int = 0,
    c: float = 6.0,
    mean0=None,
) -> Union[float, np.array]:
    """
    Calculate the weighted mean along the specified axis.

    If `data_err` is not None, it is added to the weights and then biweight location
    is computed. Otherwise, the weighted mean is equivalent to the biweight_location.
    Based on biweight location:
    https://docs.astropy.org/en/stable/api/astropy.stats.biweight.biweight_location.html

    :param data: Input data.
    :param data_err: Data uncertainty, optional.
    :param axis: Axis along which a mean is calculated.
    :param c: Tuning constant for the biweight estimator.
    :param mean0: Initial guess for mean.
    :return: Weighted mean of the input data.
    """
    if mean0 is None:
        mean0 = np.median(data, axis=axis)

    mad = median_absolute_deviation(data, axis=axis)

    d = data - mean0
    weight = d**2
    if data_err is not None:
        weight += data_err**2

    if np.isscalar(mean0) and (mad == 0.0 or np.isnan(mad)):
        correction = 0
    else:
        with np.errstate(divide="ignore", invalid="ignore"):
            u = weight / (c * mad) ** 2
            mask = u >= 1
            u = (1 - u) ** 2
            u[mask] = 0
            correction = np.sum(u * d, axis=axis) / np.sum(u, axis=axis)

    if np.isscalar(mean0):
        # if data_err is big, sum(u) could be 0 and correction is undefined
        correction = 0 if np.isnan(correction) else correction
        wmean = mean0 + correction
    else:
        correction = np.where(np.isnan(correction), 0, correction)
        wmean = mean0 + np.where(mad == 0, 0, correction)

    return wmean


def mean_and_std(
    data: np.array, data_err: np.array, axis: int = 0
) -> tuple[np.array, np.array]:
    """
    Robust estimation for the mean and std based on Tukey's biweight.

    :param data: Input data.
    :param data_err: Data uncertainty, optional.
    :param axis: Axis along which statistic is calculated.
    :return: Tuple of mean and standard deviation.
    """
    wmean0 = weighted_mean(data, data_err, axis=axis)
    wmean = weighted_mean(data, data_err, axis=axis, mean0=wmean0)
    std = biweight_scale(data, axis=axis, M=wmean)
    return wmean, std


def protein_abundance(
    df_psm: pd.DataFrame,
    groupby_cols: list,
    specimen_cols: list,
    error_cols: list = None,
) -> pd.DataFrame:
    """
    Calculate protein abundance and its standard deviation.

    The protein abundance is computed as a weighted mean of reduced intensities of PSMs.
    Standard deviation of abundance is computed by biweight_scale.

    :param df_psm: DataFrame with reduced intensities and optionally errors.
    :param groupby_cols: df_psm columns to group PSMs for a protein.
    :param specimen_cols: List of specimen columns.
    :param error_cols: List of error columns corresponding to the specimen columns,
        optional.
    :return: DataFrame of protein abundance and its std error.
    """
    if len(groupby_cols) > 1:
        multi_index = pd.MultiIndex.from_tuples(
            df_psm.groupby(groupby_cols).indices.keys(),
            names=groupby_cols,
        )
    elif len(groupby_cols) == 1:
        multi_index = pd.Index(
            df_psm.groupby(groupby_cols).indices.keys(),
            name=groupby_cols[0],
        )
    else:
        raise ValueError("`groupby_cols` must be non-empty list.")
    std_cols = [f"{col}_std" for col in specimen_cols]
    df_protein = pd.DataFrame(
        index=multi_index,
        columns=specimen_cols + std_cols,
        dtype=float,
    )
    for mi, df in df_psm.groupby(groupby_cols):
        data = np.array(df[specimen_cols])
        data_err = None if error_cols is None else np.array(df[error_cols])
        df_protein.loc[mi] = np.hstack(mean_and_std(data, data_err))
    return df_protein.reset_index()
