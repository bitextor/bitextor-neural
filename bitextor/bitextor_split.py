#!/usr/bin/env python3

#  This file is part of Bitextor.
#
#  Bitextor is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Bitextor is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Bitextor.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import argparse
import base64
import string

from sentence_splitter import SentenceSplitter, SentenceSplitterException

from bitextor.utils.common import open_xz_or_gzip_or_plain
from bitextor.utils.common import ExternalTextProcessor


# True -> keep sentence
# False -> throw away
def filter_trash(sentence):
    digits_and_punctuation = string.punctuation + string.digits
    n = 0
    for c in sentence:
        if c == "\x00":
            return False
        if c in digits_and_punctuation:
            n = n + 1
    return n < len(sentence) // 2


def split_external(text, external_splitter, prune_type="words", prune_threshold=0):
    output, error_output, returncode = external_splitter.process(content)
    if returncode != 0:
        print(f"External sentence splitter existed with non-zero code: {returncode}", file=sys.stderr)
        print(error_output.strip(), file=sys.stderr)
        sys.exit(1)

    segments = output.strip().split("\n")
    # prune long sentences
    if prune_threshold and prune_type == "words":
        segments = [s for s in segments if not len(s.split()) > prune_threshold]
    elif prune_threshold and prune_type == "chars":
        segments = [s for s in segments if not len(s) > prune_threshold]

    segments = [s for s in segments if filter_trash(s)]

    segmented_text = "\n".join(segments) + "\n"
    return segmented_text


def split_moses(text, moses_splitter, prune_type="words", prune_threshold=0):
    segments = moses_splitter.split(content)

    # prune long sentences
    if prune_threshold and prune_type == "words":
        segments = [s for s in segments if not len(s.split()) > prune_threshold]
    elif prune_threshold and prune_type == "chars":
        segments = [s for s in segments if not len(s) > prune_threshold]

    segments = [s for s in segments if filter_trash(s)]

    segmented_text = "\n".join(segments) + "\n"
    return segmented_text


oparser = argparse.ArgumentParser(description="Tool that does sentence splitting on plain text")
oparser.add_argument('--text', dest='text', help='Plain text file', default="-")
oparser.add_argument('--sentence-splitter', dest='splitter', default=None, help="Sentence splitter command line. "
                     "If not provided, Moses split_sentences Python port will be used.")
oparser.add_argument('--langcode', dest='langcode', default="en",
                     help="Language code for default sentence splitter and tokenizer")
oparser.add_argument('--customnbp', dest='customnbp',
                     help="Path for custom non breaking prefixes used by Moses Sentence Splitter Python port")
oparser.add_argument('--sentences-output', default="plain_sentences.xz", dest='sent_output',
                     help="Path of the output file that will contain sentence splitted text")
oparser.add_argument("--prune", dest="prune_threshold", type=int, default=0,
                     help="Prune sentences longer than n (words/characters)", required=False)
oparser.add_argument("--prune-type", dest="prune_type", choices={"words", "chars"}, default="words",
                     help="Prune sentences either by words or characters", required=False)

options = oparser.parse_args()

splitter = options.splitter
splitter_func = None
# no sentence splitter command provided, use moses:
if not splitter:
    splitter_func = split_moses
    try:
        if options.customnbp:
            splitter = SentenceSplitter(language=options.langcode, non_breaking_prefix_file=options.customnbp)
        else:
            splitter = SentenceSplitter(language=options.langcode)
    except SentenceSplitterException as e:
        sys.stderr.write(str(e) + "\n")
        splitter = SentenceSplitter(language='en')

# use custom sentence splitter via ExternalTextProcessor (inefficient):
else:
    splitter_func = split_external
    splitter = ExternalTextProcessor(os.path.expanduser(splitter).split())

with open_xz_or_gzip_or_plain(options.text) if options.text != "-" else sys.stdin as reader:
    for doc in reader:
        content = base64.b64decode(doc.strip()).decode("utf-8").replace("\t", " ")
        sentences = splitter_func(content, splitter, options.prune_type, options.prune_threshold)
        print(base64.b64encode(sentences.encode("utf-8")).decode("utf-8"))
