"""TMTCrunch main module."""

__all__ = [
    "filter_groupwise",
    "preprocess_peptides",
    "preprocess_psm",
    "process_single_batch",
    "process_fraction",
]


import logging
import os.path
import sys
from argparse import ArgumentParser

import numpy as np
import pandas as pd

from . import __version__
from .altsp import PrimeGroupsCollection, PsmGroup, generate_prefix_collection
from .config import (
    load_config,
    load_default_config,
    load_phospho_config,
    format_settings,
)
from .utils import (
    drop_decoys_from_protein_group,
    groupwise_qvalues,
    indicator,
    protein_abundance,
    uniq,
    mods_read_from_settings,
    mods_convert_mass_to_label,
    apply_modifications,
    load_gene_mapping,
)

logger = logging.getLogger(__name__)


def filter_groupwise(df_psm: pd.DataFrame, settings: dict) -> pd.DataFrame:
    """
    Perform qroupwise filtration of PSMs.

    :param df_psm: DataFrame of PSMs (Scavager format)
    :param settings: TMTCrunch settings.
    :return: DataFrame with filtered PSMs.
    """
    prefix_collection = generate_prefix_collection(settings["target_prefixes"])
    requested_groups = settings["psm_group"]
    primes = PrimeGroupsCollection(prefix_collection, df_psm)

    logger.info(f"Prime PSM groups:\n{primes}\n")
    dframes = {group_name: pd.DataFrame() for group_name in requested_groups.keys()}
    for group_name, group_cfg in requested_groups.items():
        group_fdr = group_cfg["fdr"]
        group_psm = PsmGroup(
            group_cfg["descr"],
            target_prefixes=group_cfg["prefixes"],
            prime_groups_collection=primes,
        )
        logger.info(f"{group_psm}\n")
        df_psm_group = groupwise_qvalues(df_psm, group_psm)

        if True:  # display number of passed PSMs for different FDR values.
            fdr_steps = 5
            passed = [
                df_psm_group[df_psm_group["group_q"] < fdr].shape[0]
                for fdr in np.linspace(group_fdr / fdr_steps, group_fdr, fdr_steps)
            ]
            logger.info(f"PSMs at fdr=[{group_fdr / fdr_steps}, {group_fdr}]: {passed}")

        df_psm_group = df_psm_group[df_psm_group["group_q"] < group_fdr]
        df_psm_group = df_psm_group[~df_psm_group["decoy"]]

        if True:  # display groupwise distribution of passed PSMs
            group_psm_passed = PsmGroup(
                f"PSMs passed at fdr={group_fdr}",
                target_prefixes=group_cfg["prefixes"],
                prime_groups_collection=PrimeGroupsCollection(
                    prefix_collection, df_psm_group
                ),
            )
            logger.info(
                f"PSMs passed at fdr={group_fdr}: {df_psm_group.shape[0]}\n"
                f"{group_psm_passed.format(False)}\n"
            )

        df_psm_group["psm_group"] = group_name
        dframes[group_name] = df_psm_group
    df_psm = pd.concat(dframes.values(), ignore_index=True)
    return df_psm


def preprocess_peptides(
    df_psm: pd.DataFrame, settings: dict, inplace: bool = True
) -> pd.DataFrame | None:
    """
    Apply modification to peptides.

    :param df_psm: DataFrame of PSMs (Scavager format).
    :param settings: TMTCrunch settings.
    :param inplace: Whether to modify the PSMs DataFrame or create a copy.
    :return: DataFrame with preprocessed peptides or None if `inplace=True`.
    """

    all_mods = settings["all_mods"]
    selective_mods = settings["selective_mods"]

    def convert_all(modifications):
        return mods_convert_mass_to_label(modifications, all_mods, unrecognized=False)

    def convert_selective(modifications):
        return mods_convert_mass_to_label(
            modifications, selective_mods, unrecognized=False
        )

    def find_unknown(modifications):
        return mods_convert_mass_to_label(modifications, all_mods, unrecognized=True)[1]

    def modify_peptide(df):
        return apply_modifications(df.iloc[0], df.iloc[1])

    if not inplace:
        df_psm = df_psm.copy()

    # peptide with selective mods only
    df_psm["modifications_pydict"] = df_psm["modifications"].apply(convert_selective)
    df_psm["modpeptide"] = df_psm[["peptide", "modifications_pydict"]].apply(
        modify_peptide, axis=1
    )
    # peptide with all mods
    df_psm["modifications_pydict"] = df_psm["modifications"].apply(convert_all)
    df_psm["peptide_all_mods"] = df_psm[["peptide", "modifications_pydict"]].apply(
        modify_peptide, axis=1
    )
    # unrecognized modifications
    df_psm["unknown_mods"] = df_psm["modifications"].apply(find_unknown)

    if not inplace:
        return df_psm


def process_fraction(df_psm: pd.DataFrame, settings: dict) -> pd.DataFrame:
    """
    Process PSMs from single fraction.

    :param df_psm: DataFrame of PSMs.
    :param settings: TMTCrunch settings.
    :return: DataFrame with filtered PSMs.
    """
    decoy_prefix = settings["decoy_prefix"]
    with_modifications = settings["with_modifications"]
    global_fdr = settings["global_fdr"]
    groupwise = settings["groupwise"]
    user_keep_cols = settings["keep_columns"]
    tmt_cols = settings["gis_columns"] + settings["specimen_columns"]
    simulate_gis_cols = settings["simulate_gis"]
    with_simulated_gis = len(settings["simulate_gis"])
    fake_gis_column = settings["gis_columns"][0]

    cols = []
    if groupwise:
        df_psm = filter_groupwise(df_psm, settings)
        cols += ["psm_group"]
    else:
        df_psm = df_psm[~df_psm["decoy"]]
        df_psm = df_psm[df_psm["PSM_q"] <= global_fdr]
    if with_modifications:
        preprocess_peptides(df_psm, settings, inplace=True)
        cols += ["modpeptide", "peptide_all_mods", "unknown_mods"]
    if with_simulated_gis:
        df_psm[fake_gis_column] = np.mean(df_psm[simulate_gis_cols], axis=1)

    df_psm["protein"] = df_psm["protein"].apply(drop_decoys_from_protein_group)
    df_psm["gene"] = ""
    df_psm["file"] = ""
    cols += [
        "peptide",
        "gene",
        "protein",
        "file",
        "modifications",
        "spectrum",
        "retention_time",
    ]
    cols += list(set(user_keep_cols) - set(cols))
    cols += tmt_cols
    return df_psm[cols]


def preprocess_psm(df_psm: pd.DataFrame, settings: dict) -> tuple[pd.DataFrame, int]:
    """
    Prepare PSMs of a single batch for merging with other batches.

    Reject PSMs with failed channels.
    Normalize tmt channel to account for loading difference.
    Reduce channel intensities with respect to GIS.

    :param df_psm: DataFrame of PSMs.
    :param settings: TMTCrunch settings.
    :return: tuple of DataFrame with preprocessed PSMs and number of rejected PSMs.
    """
    gis_cols = settings["gis_columns"]
    spn_cols = settings["specimen_columns"]
    tmt_cols = settings["gis_columns"] + settings["specimen_columns"]

    # TODO: Drop PSMs olny with failed GIS channels.
    # protein_abundance() has to be resistant to the missing values.
    # ind_gis_non_zero = indicator(df_psm, cols=gis_cols, ind_func=bool)
    ind_all_non_zero = indicator(df_psm, cols=tmt_cols, ind_func=bool)
    ind_all_finite = indicator(df_psm, cols=spn_cols, ind_func=np.isfinite)

    n_total = df_psm.shape[0]
    df_psm = df_psm[ind_all_non_zero & ind_all_finite].copy()
    n_rejected = n_total - df_psm.shape[0]

    # Normalize intensity per channel to account for loading difference.
    # If MS/MS were reproducible, sum() could be used for normalization.
    df_psm.loc[:, tmt_cols] /= np.mean(df_psm[tmt_cols], axis=0)
    # Switch to natural logarithm for further analysis.
    # The absolute error for log(x) is the relative error for x
    # due to d(log(x)) = dx/x and we like it.
    df_psm.loc[:, tmt_cols] = np.log(df_psm[tmt_cols])

    df_psm["gis_mean"] = np.mean(df_psm[gis_cols], axis=1)
    df_psm["gis_err"] = np.std(df_psm[gis_cols], axis=1)
    # Reduce individual intensities with respect to the mean GIS intensity.
    df_psm[spn_cols] -= np.array(df_psm["gis_mean"])[:, np.newaxis]
    return df_psm, n_rejected


def process_single_batch(files: list[str], settings: dict) -> dict:
    """
    Process fractions of the same batch.

    Calculate gene product and protein abundance from individual PSMs.
    Group results by PSM groups, genes, and proteins.

    :param files: Scavager *_PSMs_full.tsv files.
    :param settings: TMTCrunch settings.
    :return: dictionary of DataFrames for PSMs, proteins, and genes.
    """
    if settings["input_format"] == "sage":
        from .sage import read_fraction
    else:
        from .scavager import read_fraction

    groupwise = settings["groupwise"]
    gis_cols = settings["gis_columns"]
    spn_cols = settings["specimen_columns"]
    with_modifications = settings["with_modifications"]
    output_tables = dict.fromkeys(settings["output_tables"])
    fasta = settings["fasta_file"]

    logger.info(f"Total files in the batch: {len(files)}")
    genes = load_gene_mapping(fasta) if fasta != "" else {}
    fractions = []
    for file in files:
        logger.info(f"Processing {file}")
        df = process_fraction(read_fraction(file), settings)
        df["file"] = file
        fractions.append(df)
    df_psm = pd.concat(fractions, ignore_index=True)
    del fractions, df

    n_psm_total = df_psm.shape[0]
    df_psm, n_psm_bad = preprocess_psm(df_psm, settings)
    n_peptides = len(uniq(df_psm["peptide"].to_list(), sort=False))

    df_psm["gene"] = df_psm["protein"].apply(
        lambda proteins: uniq([genes.get(p, "_not_found") for p in proteins])
    )
    df_psm["gene"] = df_psm["gene"].apply(";".join)
    df_psm["protein"] = df_psm["protein"].apply(";".join)

    if "gis" in output_tables.keys():
        output_gis_index = ["file"]
        output_gis_index += ["psm_group"] if groupwise else []
        output_gis_index += ["gene", "protein", "peptide"]
        if with_modifications:
            output_gis_index += ["modpeptide", "peptide_all_mods"]
        output_gis_columns = ["spectrum", "retention_time"] + gis_cols
        output_tables["gis"] = (
            df_psm[output_gis_index + output_gis_columns]
            .copy()
            .sort_values(by="retention_time")
        )

    total_message = (
        f"Total PSMs:                     {n_psm_total:>7}\n"
        f"PSMs with failed channels:      {n_psm_bad:>7}\n"
        f"Total PSMs used for assembling: {df_psm.shape[0]:>7}\n"
        f"Total peptides:                 {n_peptides:>7}\n"
    )

    # Group PSMs with the same gene, protein, peptide, peptide with mods to calculate corresponding abundance.
    supported_output_tables = ["gene", "protein", "peptide", "modpeptide"]
    index_columns = ["psm_group"] if groupwise else []
    groupby_cols = {}
    for kind in supported_output_tables:
        index_columns += [kind]
        groupby_cols[kind] = index_columns.copy()

    finest_level = "modpeptide" if with_modifications else "peptide"
    df_psm.sort_values(by=groupby_cols[finest_level], inplace=True)
    df_psm_short = df_psm[groupby_cols[finest_level] + spn_cols].copy()
    # GIS error is rhe only source of error we currently account for specimen values at PSMs level.
    # Since we work with natural log(intensity) the specimen error is equal to GIS error.
    # The GIS error is undefined for data with only one GIS channel.
    spn_err_cols = None
    if len(gis_cols) >= 2:
        spn_err_cols = [f"{col}_err" for col in spn_cols]
        df_psm_short[spn_err_cols] = (
            np.ones(df_psm[spn_cols].shape) * np.array(df_psm["gis_err"])[:, np.newaxis]
        )
    # Calculate abundance at gene, protein, peptide, etc levels.
    for kind in groupby_cols.keys():
        if kind in output_tables.keys():
            logger.info(f"Calculating abundance at {kind} level.")
            output_tables[kind] = protein_abundance(
                df_psm_short,
                groupby_cols[kind],
                spn_cols,
                spn_err_cols,
            )
    # Add the number of gene and protein groups to the summary.
    for kind in ["protein", "gene"]:
        if kind in output_tables.keys():
            n_kind = output_tables[kind].shape[0]
            spacer = " " * (18 - len(kind))
            total_message += f"Total {kind} groups:{spacer}{n_kind:>7}\n"
    logger.info("Summary:\n" + total_message)

    if "psm" in output_tables.keys():
        output_tables["psm"] = df_psm
    return output_tables


def cli_main() -> None:
    parser = ArgumentParser(description=f"TMTCrunch version {__version__}")
    supported_input = ["auto", "scavager", "sage"]
    parser.add_argument(
        "fractions",
        nargs="*",
        help="Scavager *_PSMs_full.tsv files or directories with Sage search results.",
    )
    parser.add_argument(
        "--cfg",
        action="append",
        help="Path to configuration file. Can be specified multiple times.",
    )
    parser.add_argument(
        "--fasta",
        help="Path to protein fasta file for mapping protein to gene symbol.",
    )
    parser.add_argument(
        "--input-format",
        type=str,
        choices=supported_input,
        default="auto",
        help="Format of input data. Supported: "
        + ", ".join([f"'{s}'" for s in supported_input])
        + ". Default is 'auto'",
    )
    parser.add_argument(
        "--output-dir",
        "--odir",
        default="",
        help="Existing output directory. Default is current directory.",
    )
    parser.add_argument(
        "--output-prefix",
        "--oprefix",
        default="tmtcrunch_",
        help="Prefix for output files. Default is 'tmtcrunch_'.",
    )
    parser.add_argument(
        "--phospho",
        action="store_true",
        help="Enable common modifications for phospho-proteomics.",
    )
    parser.add_argument(
        "--verbose",
        type=int,
        choices=range(3),
        default=1,
        help="Logging verbosity. Default is 1.",
    )
    parser.add_argument(
        "--show-config", action="store_true", help="Show configuration and exit."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__version__}",
        help="Output version information and exit.",
    )

    cmd_args = parser.parse_args()
    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        format="{levelname}: {message}",
        datefmt="[%H:%M:%S]",
        level=log_levels[cmd_args.verbose],
        style="{",
    )

    with_gene_table = False
    settings = load_default_config()
    if cmd_args.phospho:
        settings |= load_phospho_config()
    # Supported tables: gene, protein, peptide, modpeptide, psm, gis.
    settings["output_tables"] = ["gis", "psm"]
    if cmd_args.cfg:
        for fpath in cmd_args.cfg:
            settings |= load_config(fpath)

    if cmd_args.fasta:
        settings["fasta_file"] = cmd_args.fasta

    if settings["fasta_file"] != "":
        with_gene_table = True

    if not (len(settings["gis_columns"]) or len(settings["simulate_gis"])):
        logger.error("At least one GIS column is required!")
        sys.exit(1)
    conflicting = set(settings["gis_columns"]) & set(settings["specimen_columns"])
    if conflicting:
        logger.error(f"Overlapping GIS and specimen columns: {conflicting}")
        sys.exit(1)

    # prepare for groupwise
    if settings["groupwise"]:
        for group_name, group_cfg in settings["psm_group"].items():
            if "fdr" not in group_cfg.keys():
                settings[group_name]["fdr"] = settings["global_fdr"]
    else:
        settings["psm_group"] = {}

    if settings["groupwise"] and "target_prefixes" not in settings.keys():
        target_prefixes = []
        for group_cfg in settings["psm_group"].values():
            for prefixes in group_cfg["prefixes"]:
                target_prefixes.extend(prefixes)
        settings["target_prefixes"] = uniq(target_prefixes)

    # prepare for modifications
    if settings["with_modifications"]:
        selective_mods = mods_read_from_settings(settings["modification"]["selective"])
        universal_mods = mods_read_from_settings(settings["modification"]["universal"])
        settings["selective_mods"] = selective_mods
        settings["all_mods"] = selective_mods | universal_mods
        settings["output_tables"] += ["modpeptide"]
    else:
        settings["output_tables"] += ["peptide", "protein"]
        if with_gene_table:
            settings["output_tables"] += ["gene"]

    settings["input_format"] = cmd_args.input_format
    if len(cmd_args.fractions) > 0 and cmd_args.input_format == "auto":
        is_tsv = [f.endswith("PSMs_full.tsv") for f in cmd_args.fractions]
        if all(is_tsv):
            settings["input_format"] = "scavager"
        elif not any(is_tsv):
            settings["input_format"] = "sage"
        else:
            logger.error(f"failed to detect input format: {cmd_args.fractions}")
            sys.exit(1)

    if cmd_args.show_config:
        print(f"output directory: {cmd_args.output_dir}")
        for kind in settings["output_tables"]:
            print(f"output file: {cmd_args.output_prefix}{kind}.tsv")
        print(f"verbosity: {cmd_args.verbose}")
        print(format_settings(settings))
        sys.exit()
    if len(cmd_args.fractions) == 0:
        logger.error(f"missing argument: file")
        sys.exit(1)

    logger.info(
        "Starting...\n"
        + f"TMTCrunch version {__version__}\n"
        + format_settings(settings)
    )
    if len(settings["gis_columns"]) == 1:
        logger.warning(
            "Only one GIS channel is specified. Using simplified quantification."
        )
    if len(settings["simulate_gis"]):
        settings["gis_columns"] = ["fake_gis"]

    output_tables = process_single_batch(cmd_args.fractions, settings)
    for kind, df in output_tables.items():
        fpath = os.path.join(cmd_args.output_dir, f"{cmd_args.output_prefix}{kind}.tsv")
        logger.info(f"Saving {fpath}")
        df.to_csv(fpath, sep="\t", index=False)
    logger.info("Done.")


if __name__ == "__main__":
    cli_main()
