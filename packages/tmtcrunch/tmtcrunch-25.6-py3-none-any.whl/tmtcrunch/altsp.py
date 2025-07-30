"""Classes and functions to group PSMs by the prefix in FASTA headers."""

__all__ = [
    "GeneralPsmGroup",
    "PsmGroup",
    "PrimeGroupsCollection",
    "expand_collection",
    "collection_from_elements",
    "generate_prefix_collection",
    "is_derived_superset",
]


import numpy as np
import pandas as pd


def expand_collection(new_element: str, collection: list[list[str]]) -> list[list[str]]:
    """
    Create new collection of all combinations using new element and existing collection.

    :param new_element: New element.
    :param collection: Collection.
    :return: New collection of all combinations.
    """
    expanded_collection = [[new_element]] + collection
    for combination in collection:
        expanded_collection.append([new_element] + combination)
    return expanded_collection


def collection_from_elements(list_of_elements: list) -> list[list[str]]:
    """
    Create collection of all combinations of elements.

    :param list_of_elements: List of unique elements.
    :return: Collection of all combinations of elements.
    """
    collection = []
    for element in list_of_elements:
        collection = expand_collection(element, collection)
    return collection


def generate_prefix_collection(
    target_prefixes: list[str], decoy_prefix: str = "DECOY_"
) -> list[list[str]]:
    """
    Generate list of all possible prefixes for PSMs.

    :param target_prefixes: List of target prefixes.
    :param decoy_prefix: Decoy prefix, defaults to "DECOY_".
    :return: Collection of all possible prefixes.
    """
    decoy_prefixes = [decoy_prefix + tp for tp in target_prefixes]
    all_prefixes = target_prefixes + decoy_prefixes
    return collection_from_elements(all_prefixes)


def is_derived_superset(super_set: list[str], base_set: list[str]) -> bool:
    """
    Check whether list of strings is derived from the `base_set`.

    List of strings is derived from base set if all its strings starts with any and only
    with any string from the base set.

    :param super_set: List of strings.
    :param base_set: List of base strings.
    :return: True, if `super_set` is derived from the `base_set`.
    """
    mat = [[x.startswith(s) for x in super_set] for s in base_set]
    return all(np.any(mat, axis=0)) and all(np.any(mat, axis=1))


class PrimeGroupsCollection:
    """Collection of prime PSM groups."""

    def __init__(
        self,
        prefix_collection: list[list[str]],
        df_psm: pd.DataFrame = pd.DataFrame({"protein": ["none"]}),
        decoy_prefix: str = "DECOY_",
    ):
        """
        Create collection of prime PSM groups.

        :param prefix_collection: Collection of prefixes for prime groups.
        :param df_psm: Pandas DataFrame with PSMs.
        :param decoy_prefix: Decoy prefix.
        """
        self.decoy_prefix = decoy_prefix
        self.prime_groups = {
            i: {"prefixes": v} for i, v in enumerate(prefix_collection)
        }
        self.df_psm = df_psm
        for group in self.prime_groups.values():
            group["indicator"] = df_psm.protein.apply(
                lambda x: is_derived_superset(x, group["prefixes"])
            )
            group["count"] = sum(group["indicator"])
        self.total_psm = sum(group["count"] for group in self.prime_groups.values())
        self.unaccounted_psm = self.df_psm.shape[0] - self.total_psm

    def __str__(self) -> str:
        buffer = "key      PSMs   Prime PSM group\n"
        for k, group in self.prime_groups.items():
            buffer += f"{k:>2} {group['count']:>10}   {group['prefixes']}\n"
        buffer += f"\nTotal psm: {self.total_psm}"
        if self.unaccounted_psm:
            buffer += f"\nUnaccounted PSM: {self.unaccounted_psm}"
        return buffer

    def get_prime_groups_for_prefixes(
        self, target_prefixes: list[list[str]]
    ) -> tuple[list[int], list[int]]:
        """
        Return prime PSM groups for the general PSM group defined by its target
        prefixes.

        :param target_prefixes: Collection of prefixes to identify target PSM.
        :return: List of keys for decoy prime groups and list of keys for target groups.
        """
        decoy_keys = []
        target_keys = []
        for i, group in self.prime_groups.items():
            for bunch in target_prefixes:
                if is_derived_superset(
                    group["prefixes"],
                    [self.decoy_prefix + target_prefix for target_prefix in bunch],
                ):
                    decoy_keys.append(i)
                if is_derived_superset(group["prefixes"], [self.decoy_prefix] + bunch):
                    target_keys.append(i)
                if is_derived_superset(group["prefixes"], bunch):
                    target_keys.append(i)
        return decoy_keys, target_keys


class GeneralPsmGroup:
    """General PSM group defined by arbitrary prime groups."""

    def __init__(
        self,
        label: str,
        decoy_keys: list[int],
        target_keys: list[int],
        prime_groups_collection: PrimeGroupsCollection,
    ):
        """
        Group PSMs by arbitrary prime groups.

        :param label: Group label.
        :param decoy_keys: Keys of decoy prime groups.
        :param target_keys: Keys of target prime groups.
        :param prime_groups_collection: Instance of `PrimeGroupsCollection`.
        """
        self.label = label
        self.decoy_keys = decoy_keys
        self.target_keys = target_keys
        self.df_psm = prime_groups_collection.df_psm
        self.prime_groups = prime_groups_collection.prime_groups

        self.decoy_ind = self.prime_groups[self.decoy_keys[0]]["indicator"]
        for i in self.decoy_keys[1:]:
            self.decoy_ind = self.decoy_ind | self.prime_groups[i]["indicator"]

        self.target_ind = self.prime_groups[target_keys[0]]["indicator"]
        for i in target_keys[1:]:
            self.target_ind = self.target_ind | self.prime_groups[i]["indicator"]

        total_decoy_psm = sum(self.prime_groups[i]["count"] for i in self.decoy_keys)
        self.total_target_psm = sum(
            self.prime_groups[i]["count"] for i in self.target_keys
        )
        self.total_psm = total_decoy_psm + self.total_target_psm
        self.percent_factor = 100 / max(self.df_psm.shape[0], 1)
        self.table_header = "key      PSMs         %  Prime PSM group"

    def __str__(self) -> str:
        return self.format(verbose=False)

    def __format_subgroup(self, subgroup_keys: list[int], label: str = None) -> str:
        """Format subgroup for printing."""
        buffer = f"    =={label:^20}==\n" if label else ""
        for i in subgroup_keys:
            count = self.prime_groups[i]["count"]
            percent = self.percent_factor * self.prime_groups[i]["count"]
            buffer += f"{i:>2} {count:>10}   {percent:>7.2f}  {self.prime_groups[i]['prefixes']}\n"
        return buffer[:-1]

    def format(self, verbose=False) -> str:
        """
        Return formatted representation of class instance.

        :param verbose: Show header, decoy subgroup and overall stats.
        :return: Formatted string.
        """
        buffer = self.table_header + "\n"
        if verbose:
            buffer += self.__format_subgroup(self.decoy_keys, "Decoy subgroup")
            buffer += "\n"
            buffer += self.__format_subgroup(self.target_keys, "Target subgroup")
            buffer += "\n\n"
            percent = self.percent_factor * self.total_target_psm
            buffer += (
                f"Total target PSMs: {self.total_target_psm:>10} ({percent:>5.2f}%)\n"
            )
            percent = self.percent_factor * self.total_psm
            buffer += f"Total PSMs:        {self.total_psm:>10} ({percent:>5.2f}%)"
        else:
            buffer += self.__format_subgroup(self.target_keys)
        return buffer


class PsmGroup(GeneralPsmGroup):
    """Group of PSMs defined by collection of its target prefixes."""

    def __init__(
        self,
        label: str,
        target_prefixes: list[list[str]],
        prime_groups_collection: PrimeGroupsCollection,
    ):
        """
        Group PSMs by collection of target prefixes.

        :param label: Group label.
        :param target_prefixes: Collection of target prefixes.
        :param prime_groups_collection: Instance of `PrimeGroupsCollection`.
        """
        self.target_prefixes = target_prefixes
        decoy_keys, target_keys = prime_groups_collection.get_prime_groups_for_prefixes(
            self.target_prefixes
        )
        super().__init__(
            label=label,
            decoy_keys=decoy_keys,
            target_keys=target_keys,
            prime_groups_collection=prime_groups_collection,
        )

    def __str__(self) -> str:
        return self.format(verbose=True)

    def format(self, verbose=False) -> str:
        """
        Return formatted representation of class instance.

        :param verbose: Show header and additional info.
        :return: Formatted string.
        """
        buffer = f"{self.label}: {self.target_prefixes}\n" if verbose else ""
        buffer += super().format(verbose)
        return buffer
