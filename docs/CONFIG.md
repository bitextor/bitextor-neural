# Bitextor configuration file

Bitextor uses a configuration file to define the variables required by the pipeline. Depending on the options defined in this configuration file the pipeline can behave differently, running alternative tools and functionalities. The following is an exhaustive overview of all the options that can be set in the configuration file and how they affect to the pipeline.

**Suggestion**: A minimalist [configuration file sample](config/basic.yaml) is provided in this repository. You can take it as an starting point by changing all the paths to match your environment.

Current pipeline constists of the following steps:

* Crawling
* Plain text extraction
* Sharding
* Sentence splitting
* Document alignment
* Segment alignment
* Cleaning and filtering

Following is a description of configuration related to each step, as well as basic variables.

## Data storage

There are a few variables that are mandatory for running Bitextor, independently of the task to be carried out, namely the ones related to where final & intermediate files should be stored.

```yaml
permanentDir: ~/permanent/bitextor-output
dataDir: ~/permanent/data
transientDir: ~/transient
tempDir: ~/transient
```

* `permanentDir`: will contain the final results of the run, i.e. the parallel corpus built
* `dataDir`: will contain the results of crawling (WARC files) and files generated during preprocessing (plain text extraction, sharding, sentence splitting, tokenisation and translation), i.e. every step up to document alignment
* `transientDir`: will contain the results of intermediate steps related to document and sentence alignment, as well as cleaning
* `tempDir`: will contain temporary files that are needed by some steps and removed immediately after they are no longer required

## Workflow execution

There are some optional parameters that allow for a finer control of the execution of the pipeline, namely it is possible to configure some jobs to use more than one core; and it is possible to have a partial execution of Bitextor by specifying what step should be final.

```yaml
until: preprocess
parallelWorkers: {split: 2, docalign: 8, segaling: 8, bicleaner: 2}
profiling: true
```

* `until`: pipeline executes until specified step and stops. The resulting files will not necessarily be in `permanentDir`, they can also be found in `dataDir` or `transientDir` depending on the rule. Allowed values: `crawl`, `preprocess`, `shard`, `split`, `translate`, `tokenise_src`, `tokenise_trg`, `docalign`, `segalign`, `bifixer`, `bicleaner`, `filter`
* `parallelWorkers`: a dictionary specifying the number of cores that should be used for a job. Allowed values: `split`, `translate`, `tokenise_src`, `tokenise_trg`, `docalign`, `segalign`, `bifixer`, `bicleaner`, `sents`
* `profiling`: use `/usr/bin/time` tool to obtain profiling information about each step.

## Data sources

The next set of option srefer to the source from which data will be harvested. It is possible to specify a list of websites to be crawled and/or a list of [WARC](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1) files that contain pre-crawled websites.
Both can be specified either via a list of source directly in the config file, or via a separated gzipped file that contains one source per line.

```yaml
hosts: ["www.elisabethtea.com","vade-antea.fr"]
hostsFile: ~/hosts.gz

warcs: ["/path/to/a.warc.gz", "/path/to/b.warc.gz"]
warcsFile: ~warcs.gz
```

* `hosts`: list of [hosts](https://en.wikipedia.org/wiki/URL) to be crawled; the host is the part of the URL of a website that identifies the web domain, i.e. the URL without the protocol and the path. For example, in the case of the url *<https://github.com/bitextor/bitextor>* the host would be *github.com*
* `hostsFile`: a path to a file that contains a list of hosts to be crawled; in this file each line should contain a single host, written in the format described above.
* `warcs`: specify one or multiple [WARC](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1) files to use; WARC files must contain individually compressed records
* `warcsFile`: a path to a file that contains a list of WARC files to be included in parallel text mining (silimar to `hosts` and `hostsFile`)

## Crawling

There are different options supported in order to configure the crawler. Specificaly, the only crawler supported is `wget`. `wget` will launch a crawling job for each specified host, which will be finished either when there is nothing more to download or the specified time limit has been reached. The following parameters may be configured when using this tool:

```yaml
crawlTimeLimit: 1h
crawlerUserAgent: "Mozilla/5.0 (compatible; Bitextor/8 +https://github.com/bitextor/bitextor)"
crawlWait: 5
crawlFileTypes: ["html", "pdf"]
```

* `crawlTimeLimit`: time for which a website can be crawled; the format of this field is an integer number followed by a suffix indicating the units (accepted units are s(seconds), m(minutes), h(hours), d(days), w(weeks)), for example: `86400s`, or `1440m` or `24h`, or `1d`.
* `crawlerUserAgent`: [user agent](https://developers.whatismybrowser.com/useragents/explore/software_type_specific/crawler/) to be added to the header of the crawler when doing requests to a web server (identifies your crawler when downloading a website).
* `crawlWait`: time (in seconds) that should be waited between the retrievals; it is intended to avoid a web-site to cut the connection of the crawler due too many connections in a low interval of time.
* `crawlFileTypes`: filetypes that sould be retrieved; `wget` will check the extension of the document.

## Preprocessing and sharding

After crawling, the downloaded webs are processed to extract clean text, detect language, etc.

After plain text extracion, the extracted data is sharded via [giashard](https://github.com/paracrawl/giashard) in order to create balanced jobs.
Crawled websites and WARCs are distributed in shards for a more balanced processing, where each shard contains one or more complete domain(s).
Shards in turn are split into batches of specified size to keep memory consumption in check.
Document alignemnt works within shards, i.e. all documents in a shard will be compared for document alignment.

The following set of option define how that process is carried out.

```yaml
# preprocessing
preprocessor: warc2text
langs: [en, es, fr]

# sharding
shards: 8 # 2^8 shards
batches: 1024 # batches of up to 1024MB
```

* `preprocessor`: this options allows to select one of two text extraction tools, `warc2text` (default) or `warc2preprocess`. `warc2text` is faster but less flexibile (less options) than `warc2preprocess`. There is another preprocessor, but cannot be set, and that is `prevertical2text`. This preprocessor will be used automatically when you have prevertical files, which is the format of the SpiderLing crawler. The reason why cannot be set is because is not a generic preprocessor, but specific for SpiderLing files.
* `langs`: list of languages that will be processed in addition to `lang1` and `lang2`.

Options specific to `warc2preprocess`:

* `langID`: the model that should be used for language identification, [`cld2`](https://github.com/CLD2Owners/cld2) (default) or [`cld3`](https://github.com/google/cld3); `cld2` is faster, but `cld3` can be more accurate for certain languages
* `ftfy`: ftfy is a tool that solves encoding errors (disabled by default)
* `cleanHTML`: attempt to remove some parts of HTML that don't contain text (such as CSS, embedded scripts or special tags) before running ftfy, which is a quite slow, in order to improve overall speed; this has an unwanted side effect of removing too much content if the HTML document is malformed (disabled by default)
* `html5lib`: extra parsing with [`html5lib`](https://pypi.org/project/html5lib/), which is slow but the cleanest option and parses the HTML the same way as the modern browsers, which is interesting for broken HTMLs (disabled by default)
* `boilerplateCleaning`: enable [boilerpipe](https://boilerpipe-web.appspot.com/) to remove boilerplates from HTML documents (disabled by default)
* `parser`: select HTML parsing library for text extraction; options are: [`bs4`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) (default), [`modest`](https://github.com/rushter/selectolax), `lxml` (uses `html5lib`) or `simple` (very basic HTML tokenizer)
* `PDFextract`: use [PDFExtraxt](https://github.com/bitextor/python-pdfextract) instead of poppler `pdf2html` converter
* `PDFextract_configfile`: set a path for a PDFExtract config file, specially for language models for a better sentence splitting (see [more info](https://github.com/bitextor/pdf-extract/#pdfextractjson))
* `PDFextract_sentence_join_path`: set a path for sentence-join.py script, otherwise, the one included with bitextor will be used
* `PDFextract_kenlm_path`: set path for kenlm binaries
<!-- * `plainTextHashes`: file with plain text MurmurHashes from a previous Bitextor run, so only hashes that are not found in this file are processed in Bitextor. This is useful in case you want to fully recrawl a domain but only process updated content. Works with `bitextor-warc2preprocess` -->

Boilerplate:

* `boilerplateCleaning`: if `preprocessor: warc2preprocess`, enables [boilerpipe](https://boilerpipe-web.appspot.com/) to remove boilerplates from HTML documents. If you have provided `preverticals` files, it will discard those entries detected as boilerplate by `prevertical2text` automatically. `warc2text` does not support this option. It is disabled by default

Sharding options:

* `shards`: set number of shards, where a value of 'n' will result in 2^n shards, default is 8 (2^8 shards); `shards: 0` will force all domains to be compared for alignment
* `batches`: batch size in MB, default is 1024; large batches will increase memory consumption during document alignment, but will reduce time overhead

## Sentence splitting

By default a Python port of [Moses `split-sentences.perl`](https://pypi.org/project/sentence-splitter/) will be used for sentence splitting. This is recommened even without language support, since it is possible to provide custom non-breaking prefixes. External sentence splitter can by used via `sentence-splitters` parameter (less efficient).

Custom sentence splitters must read plain text documents from standard input and write one sentence per line to standard output.

```yaml
sentenceSplitters: {
  'fr': '/home/user/bitextor/preprocess/moses/ems/support/split-sentences.perl -q -b -l fr',
  'default': '/home/user/bitextor/bitextor/example/nltk-sent-tokeniser.py english'
}

customNBPs: {
  'fr': '/home/user/bitextor/myfrenchnbp.txt'
}
```

* `sentenceSplitters`: provide custom scripts for sentence segmentation per language, script specified under `default` will be applied to all lanuages
* `customNBPs`: provide a set of files with custom Non-Breaking Prefixes for the default sentence-splitter; see [already existing files](https://github.com/berkmancenter/mediacloud-sentence-splitter/tree/develop/sentence_splitter/non_breaking_prefixes) for examples

## Tokenisation

[Moses `tokenizer.perl`](https://github.com/moses-smt/mosesdecoder/blob/master/scripts/tokenizer/tokenizer.perl) is the default tokeniser, which is used through an efficient Python wrapper. This is the recommended option unless a language is not supported.

Custom scripts for tokenisation must read sentences from standard input and write the same number of tokenised sentences to standard output.

```yaml
wordTokenizers: {
  'fr': '/home/user/bitextor/mytokenizer -l fr',
  'default': '/home/user/bitextor/moses/tokenizer/my-modified-tokenizer.perl -q -b -a -l en'
}
```

* `wordTokenizers`: scripts for word-tokenization per language, `default` script will be applied to all languages.

Tokenisation is only applied when you set `biroamer: true`.

## Document alignment

From this step forward, bitextor works with a pair of languages, which are specified through `lang1` and `lang2` parameters. The output will contain the sentence pairs in that order.

```yaml
lang1: es
lang2: en
```

The main strategy implemented in Bitextor for document aligner is based on a neural approach. Specificaly, the used tool is [Neural Document Aligner](https://github.com/bitextor/neural-document-aligner/) (NDA), which uses sentence-level embeddings and transform them to document-level embeddings. Once the document-level embeddings are available, it applies different strategies to generate the scores and get the best matches of documents.

```yaml
documentAlignerThreshold: 0.7
embeddingsBatchSizeGPU: 2048
```

* `documentAlignerThreshold`: threshold for filtering pairs of documents with a score too low, values in [0,1] range; default is 0.7
* `embeddingsBatchSizeGPU`: value which will set the batch size for the GPU when generating embeddings; default is 32

## Segment alignment

After document alignment, the next step in the pipeline is segment alignment. This will be carried out by [Vecalign](https://github.com/bitextor/vecalign). Vecalign will use sentence-level embeddings and will apply different optimizations in order to apply an optimized edit distance and get the best matches of 1-many, many-1 and many-many sentences.

```yaml
sentenceAlignerThreshold: 0.1
embeddingsBatchSizeGPU: 2048
```

* `sentenceAlignerThreshold`: threshold for filtering pairs of sentences with a score too low, values in [0,1] range; default is 0.0

## Parallel data filtering

Parallel data filtering is carried out with [Bicleaner AI](https://github.com/bitextor/bicleaner-ai); this tool uses a pre-trained regression model to filter out pairs of segments with a low confidence score.

A number of pre-trained models for Bicleaner AI are available [here](https://github.com/bitextor/bicleaner-ai-data/releases/latest). They are ready to be downloaded and decompressed.

The options required to make it work are:

```yaml
bicleaner: /home/user/bicleaner-model/en-fr/metadata.yaml
bicleanerThreshold: 0.6
```

* `bicleaner`: path to the YAML configuration file of a pre-trained model
* `bicleanerThreshold`: threshold to filter low-confidence segment pairs, accepts values in [0,1] range; default is 0.0 (no filtering). It is recommended to set it to values in [0.5,0.7]

## Post-processing

Some other options can be configured to specify the output format of the parallel corpus:

```yaml
bifixer: true
elrc: true

tmx: true
deduped: false

biroamer: true
biroamerOmitRandomSentences: true
biroamerMixFiles: ["/home/user/file-tp-mix1", "/home/user/file-to-mix2"]
biroamerImproveAlignmentCorpus: /home/user/Europarl.en-fr.txt
```

* `bifixer`: use [Bifixer](https://github.com/bitextor/bifixer) to fix parallel sentences and tag near-duplicates for removal <!-- When using `bifixer: true` it is possible to specify additional arguments using `bifixerOptions` variable. More information about these arguments in [Bifixer](https://github.com/bitextor/bifixer) repository. -->
* `elrc`: include some ELRC quality indicators in the final corpus, such as the ratio of target length to source length; these indicators can be used later to filter-out some segment pairs manually
* `tmx`: generate a [TMX](https://en.wikipedia.org/wiki/Translation_Memory_eXchange) translation memory of the output corpus
* `deduped`: generate a de-duplicated tmx and regular versions of the corpus; the tmx corpus will contain a list of URLs for the sentence pairs that were found in multiple websites
* `biroamer`: use [Biroamer](https://github.com/bitextor/biroamer) to ROAM (randomize, omit, anonymize and mix) the parallel corpus; in order to use this `tmx: true` or `deduped: true` will be necessary
* `biroamerOmitRandomSentences`: omit close to 10% of the tmx corpus
* `biroamerMixFiles`: use extra sentences to improve anonymization, this option accepts a list of files which will add the stored sentences, the files are expected to be in Moses format
* `biroamerImproveAlignmentCorpus`: an alignment corpus can be provided in order to improve the entities detection; expected to be in Moses format.

NOTE: In case you need to convert a TMX to a tab-separated plain-text file (Moses format), you could use [TMXT](https://github.com/sortiz/tmxt) tool.
