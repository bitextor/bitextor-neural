# Warning
Be aware that this repository, Bitextor Neural, has been **archived** and now is **read-only**. Features from this tool are now integrated into [Bitextor](https://github.com/bitextor/bitextor), and new features and fixes will not be ported to this repository from Bitextor.

# ![Bitextor](img/banner.png)

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
[![Chat on Discord](https://camo.githubusercontent.com/b4175720ede4f2621aa066ffbabb70ae30044679/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f636861742d446973636f72642d627269676874677265656e2e737667)](https://discord.gg/etYDaZm)
[![Snakemake](https://img.shields.io/badge/snakemake-≥6.5.3-brightgreen.svg?style=flat)](https://snakemake.readthedocs.io)

Bitextor Neural is a tool to automatically harvest bitexts from multilingual websites. To run it, it is necessary to provide:

1. The source where the parallel data will be searched: one or more websites (namely, Bitextor Neural needs [website hostnames](https://en.wikipedia.org/wiki/URL) or [WARC files](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1/))
2. The two languages on which the user is interested: language IDs must be provided following the [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)

## Installation

Bitextor Neural can be installed from source. See [instructions here](INSTALL.md).

## Usage

```text
usage: bitextor-neural [-C FILE [FILE ...]] [-c KEY=VALUE [KEY=VALUE ...]]
                       [-j JOBS] [-k] [--notemp] [--dry-run] [--forceall]
                       [--forcerun TARGET [TARGET ...]] [-q] [-h]

launch Bitextor Neural

Bitextor Neural config:
  -C FILE [FILE ...], --configfile FILE [FILE ...]
                        Bitextor Neural YAML configuration file
  -c KEY=VALUE [KEY=VALUE ...], --config KEY=VALUE [KEY=VALUE ...]
                        Set or overwrite values for Bitextor Neural config

Optional arguments:
  -j JOBS, --jobs JOBS  Number of provided cores
  -k, --keep-going      Go on with independent jobs if a job fails
  --notemp              Disable deletion of intermediate files marked as
                        temporary
  --dry-run             Do not execute anything and display what would be done
  --forceall            Force rerun every job
  --forcerun TARGET [TARGET ...]
                        List of files and rules that shall be re-created/re-
                        executed
  -q, --quiet           Do not print job information
  -h, --help            Show this help message and exit
```

## Advanced usage

Bitextor Neural uses [Snakemake](https://snakemake.readthedocs.io/en/stable/index.html) to define Bitextor's workflow and manage its execution. Snakemake provides a lot of flexibility in terms of configuring the execution of the pipeline. For advanced users that want to make the most out of this tool, `bitextor-neural-full` command is provided that calls Snakemake CLI with Bitextor Neural's workflow and exposes all of Snakemake's parameters.

### Execution on a cluster

To run Bitextor Neural on a cluster with a software that allows to manage job queues, it is recommended to use `bitextor-neural-full` command and use [Snakemake's cluster configuration](https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles).

## Bitextor Neural configuration

Bitextor Neural uses a configuration file to define the variables required by the pipeline. Depending on the options defined in this configuration file the pipeline can behave differently, running alternative tools and functionalities. For more information consult this [exhaustive overview](CONFIG.md) of all the options that can be set in the configuration file and how they affect the pipeline.

**Suggestion**: A minimalist [configuration file sample](config/basic.yaml) is provided in this repository. You can take it as an starting point by changing all the paths to match your environment.

## Bitextor Neural output

Bitextor Neural generates the final parallel corpora in multiple formats. These files will be placed in `permanentDir` folder and will have the following format: `{lang1}-{lang2}.{prefix}.gz`, where `{prefix}` corresponds to a descriptor of the corresponding format. The list of files that may be produced is the following:

* `{lang1}-{lang2}.raw.gz` - default (always generated)
* `{lang1}-{lang2}.sent.gz` - default
* `{lang1}-{lang2}.not-deduped.tmx.gz` - generated if `tmx: true`
* `{lang1}-{lang2}.deduped.tmx.gz` - generated if `dedup: true`
* `{lang1}-{lang2}.deduped.txt.gz` - generated if `dedup: true`
* `{lang1}-{lang2}.deduped-roamed.tmx.gz` - generated if `biroamer: true` and `dedup: true`
* `{lang1}-{lang2}.not-deduped-roamed.tmx.gz` - generated `biroamer: true`, `tmx: true`
and `dedup: false`

See [detailed description](OUTPUT.md) of the output files.

## Pipeline description

Bitextor Neural is a pipeline that runs a collection of scripts to produce a parallel corpus from a collection of multilingual websites. The pipeline is divided in five stages:

1. **Crawling**: documents are downloaded from the specified websites
2. **Pre-processing**: downloaded documents are normalized, boilerplates are removed, plain text is extracted, and language is identified
3. **Document alignment**: parallel documents are identified. The main implemented strategy is based on neural technologies, and specificaly, [Neural Document Aligner](https://github.com/bitextor/neural-document-aligner/) (NDA) is applied. The NDA uses sentence-level embeddings and transform them to document-level embeddings in order to calculate a score which will be used to match the documents.
4. **Segment alignment**: each pair of documents is processed to identify parallel segments. Again, the main implemented strategy is based on neural technologies, and specificaly, [Vecalign](https://github.com/bitextor/vecalign) is applied. Vecalign uses sentence-level embeddings, and with them, it applies different strategies to apply an optimized edit distance which allows to obtain matches among the sentences from 1-many, many-1 and many-many.
5. **Post-processing**: final steps that allow to clean the parallel corpus obtained using the tool [Bicleaner AI](https://github.com/bitextor/bicleaner-ai), deduplicates translation units, and computes additional quality metrics. Also, Bicleaner AI uses neural technologies, and there are [pre-trained models](https://github.com/bitextor/bicleaner-ai-data/releases) available.

___
![Connecting Europe Facility](img/logo_en_cef273x39_nonalpha.png)

All documents and software contained in this repository reflect only the authors' view. The Innovation and Networks Executive Agency of the European Union is not responsible for any use that may be made of the information it contains.
