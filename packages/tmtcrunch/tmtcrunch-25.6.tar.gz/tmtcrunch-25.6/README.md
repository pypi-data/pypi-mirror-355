# TMTCrunch

TMTCrunch is an open-source Python utility for tandem mass tag proteomics.


## Overview

TMTCrunch is designed primarily to analyze products of alternative splicing in TMT (tandem mass tag) proteomics and phospho-proteomics data.
TMTCrunch performs:
 - per channel normalization;
 - normalization across channels using inherent or virtual GIS channels as a reference;
 - optional grouping of PSMs in accordance with user defined rules;
 - global or per group FDR filtration;
 - calculation of abundance at any level: unmodified peptide, peptide with modifications, protein, gene.

TMTCrunch can be used with [Sage](https://github.com/lazear/sage) search engine or with [IdentiPy](https://github.com/levitsky/identipy)/[Scavager](https://pypi.org/project/Scavager/).


## Installation

### Installing from PyPI

The latest released version can be installed from the [Python Package Index](https://pypi.org/project/tmtcrunch):
```shell
pip install tmtcrunch
```


### Installing from source

The cutting edge version can be installed directly from the source repository:
```shell
pip install git+https://codeberg.org/makc/tmtcrunch.git
```
Alternatively, clone the repo and install the package in [development mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):
```shell
git clone https://codeberg.org/makc/tmtcrunch.git
pip install --editable tmtcrunch
```


## Dependencies

TMTCrunch relies on the following Python packages:
- [numpy](https://pypi.org/project/numpy/)
- [pandas](https://pypi.org/project/pandas/)
- [pyteomics](https://pypi.org/project/pyteomics/)
- [tomli](https://pypi.org/project/tomli/) (required only for Python < 3.11)

and it would use statistics functions from [astropy](https://pypi.org/project/astropy/) package if available.


## Command line options

```
usage: tmtcrunch [-h] [--cfg CFG] [--fasta FASTA] [--input-format {auto,scavager,sage}]
                 [--output-dir OUTPUT_DIR] [--output-prefix OUTPUT_PREFIX] [--phospho]
                 [--verbose {0,1,2}] [--show-config] [--version]
                 [fractions ...]

positional arguments:
  fractions             Scavager *_PSMs_full.tsv files or directories with Sage search results.

options:
  -h, --help            show this help message and exit
  --cfg CFG             Path to configuration file. Can be specified multiple times.
  --fasta FASTA         Path to protein fasta file for mapping protein to gene symbol.
  --input-format {auto,scavager,sage}
                        Format of input data. Supported: 'auto', 'scavager', 'sage'. Default is
                        'auto'
  --output-dir OUTPUT_DIR, --odir OUTPUT_DIR
                        Existing output directory. Default is current directory.
  --output-prefix OUTPUT_PREFIX, --oprefix OUTPUT_PREFIX
                        Prefix for output files. Default is 'tmtcrunch_'.
  --phospho             Enable common modifications for phospho-proteomics.
  --verbose {0,1,2}     Logging verbosity. Default is 1.
  --show-config         Show configuration and exit.
  --version             Output version information and exit.
```


## Configuration files

TMTCrunch stores its configuration in [TOML](https://toml.io) format.

Default TMTCrunch configuration:
```TOML
# Specimen columns.
specimen_columns = []
# Global internal standard (GIS) columns (for multi batch experiments).
gis_columns = []
# Simulate GIS via selected specimen columns.
# Intended for singe batch experiments only!
simulate_gis = []

# Prefix of decoy proteins.
decoy_prefix = 'DECOY_'

# Path to protein fasta file for mapping protein to gene symbol.
fasta_file = ''

# List of column names from input files to save in the output.
keep_columns = []

# If true, perform PSM groupwise analysis.
groupwise = true

# Global false discovery rate. Can be overwritten per PSM group.
global_fdr = 0.01

# If true, respect peptide modifications and terminate analysis at peptide level.
with_modifications = false

# No modifications by default. Run TMTCrunch with --phospho argument
# to enable common modifications for phospho-proteomics.
[modification.universal]
[modification.selective]

# Keys below are only applicable if groupwise analysis is requested.
# Prefixes of target proteins. If not set, `target_prefixes` will be deduced
# from the prefixes of PSM groups.
# target_prefixes = ['alt_', 'canon_']

# Each PSM group is named after its subkey and defined by three keys:
# `descr` - group description
# `prefixes` - prefixes of target proteins
# `fdr` - groupwise false discovery rate. If not set, global FDR will be used.

# Isoform PSMs: protein group of each PSM consists of target proteins
# with 'alt_' prefix only and any decoy proteins.
[psm_group.isoform]
descr = 'Isoform PSMs'
prefixes = [['alt_']]
fdr = 0.05

# Canonical PSMs: protein group of each PSM consists of target proteins
# with 'canon_' prefix only and any decoy proteins.
[psm_group.canon]
descr = 'Canonical PSMs'
prefixes = [['canon_']]
fdr = 0.01

# Shared PSMs: protein group of each PSM consists both of
# 'canon_' and 'alt_' target proteins and any decoy proteins.
[psm_group.shared]
descr = 'Shared PSMs'
prefixes = [['canon_', 'alt_']]
fdr = 0.01
```

Additional configuration for phospho-proteomics (use `--phospho` argument to enable):
```TOML
with_modifications = true

# Modifications can be either universal or selective. PSMs for modified
# peptides with any universal modification and the same pattern of selective
# modifications are treated together, PSMs for peptides with different pattern
# of selective modifications are treated separately.

[modification.universal.1]
name = "Carboxyamidomethylation"
mass = "160.031"
modX = "camC"

[modification.universal.2]
name = "TMTplex at K"
mass = "357.258"
modX = "tK"

[modification.universal.3]
name = "TMTplex n-term"
mass = "230.171"
modX = "t-"

[modification.universal.4]
name = "Oxidation"
mass = "147.035"
modX = "oxM"

[modification.selective.5]
name = "Phosphorylation S"
mass = "166.998"
modX = "pS"

[modification.selective.6]
name = "Phosphorylation T"
mass = "181.014"
modX = "pT"

[modification.selective.7]
name = "Phosphorylation Y"
mass = "243.030"
modX = "pY"
```


## License

TMTCrunch is distributed under the three clause BSD License.


## Related software

 - [Pyteomics](https://github.com/levitsky/pyteomics) - Python framework for proteomics data analysis.
 - [IdentiPy](https://github.com/levitsky/identipy) - search engine for bottom-up proteomics.
 - [Sage](https://github.com/lazear/sage) - proteomics search engine & quantification tool.
 - [Scavager](https://pypi.org/project/Scavager/) - proteomics post-search validation tool.
