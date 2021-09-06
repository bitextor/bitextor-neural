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

import os
import sys
import base64
import argparse
import subprocess

def get_full_path(path):
    return os.path.realpath(os.path.expanduser(path))

def check_vecalign_files(vecalign_dir):
    necessary_files = ["overlap.py", "vecalign.py"]

    for file in necessary_files:
        if not os.path.isfile(f"{vecalign_dir}/{file}"):
            raise Exception(f"necessary vecalign file not found: {file}")

def preprocess_file_content(content, return_list=False):
    result = filter(lambda line: line != "", map(lambda line: line.strip(), content.split("\n") if isinstance(content, str) else content))

    if return_list:
        return list(result)

    return result

def process_nda_output(input_file, output_file, input_is_base64):
    output = []
    src_sentences, trg_sentences = [], []
    src_idxs, trg_idxs = set(), set()

    # Read the output file
    if output_file == "-":
        # Read from stdin
        for line in sys.stdin:
            output.append(line.strip())
    else:
        with open(output_file) as file:
            output.extend(preprocess_file_content(file.readlines()))

    # Process the output
    for row in output:
        values = row.split("\t")

        if len(values) not in (2, 3):
            raise Exception(f"unexpected NDA output format. Expected columns was 3|2, got {len(values)}")

        try:
            src_idx, trg_idx = int(values[0]), int(values[1])

            src_idxs.add(src_idx)
            trg_idxs.add(trg_idx)
        except ValueError as e:
            raise Exception("could not parse the columns from the NDA output to int (wrong format?)") from e

    # Get the documents
    file = sys.stdin
    file_open = False
    total_src_files = 0
    total_trg_files = 0

    if input_file != "-":
        file = open(input_file)
        file_open = True

    for line in file:
        line = line.strip().split("\t")
        sentences = []

        if len(line) != 3:
            raise Exception(f"unexpected NDA input format. Expected columns was 3, got {len(line)}")

        # Get decoded Base64 value if needed
        if input_is_base64:
            sentences.extend(preprocess_file_content(base64.b64decode(line[0]).decode("utf-8")))
        # Read the files
        else:
            with open(line[0]) as doc:
                sentences.extend(preprocess_file_content(doc.readlines()))

        if line[2] == "src":
            # Check if the current sentence is one of the results from the output file
            if total_src_files in src_idxs:
                src_sentences.extend(sentences)

            total_src_files += 1
        elif line[2] == "trg":
            # Check if the current sentence is one of the results from the output file
            if total_trg_files in trg_idxs:
                trg_sentences.extend(sentences)

            total_trg_files += 1
        else:
            raise Exception(f"unexpected NDA input format. Expected 3rd column was src|trg, got {line[2]}")

    if file_open:
        file.close()

    return src_sentences, trg_sentences

def vecalign_overlap(vecalign_dir, sentences_path, overlaps_output_path, overlaps_output_embeddings_path, lang, num_overlaps):
    # Generate overlapping file
    result = subprocess.run([f"{vecalign_dir}/overlap.py", "-i", sentences_path, "-o", overlaps_output_path, "-n", str(num_overlaps)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result.returncode != 0:
        raise Exception(f"something went wrong while generating the overlapping files for Vecalign: return code is {result.returncode}")

    if not os.path.isfile(overlaps_output_path):
        raise Exception(f"overlap file {overlaps_output_path} should exist, but it does not exist")

    # Generate embeddings (LASER)
    if "LASER" not in os.environ:
        raise Exception("Envvar LASER is not defined")

    laser_path = os.environ["LASER"]
    result = subprocess.run([f"{laser_path}/tasks/embed/embed.sh", overlaps_output_path, lang, overlaps_output_embeddings_path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result.returncode != 0:
        raise Exception(f"something went wrong while generating the embeddings for the overlapping files: return code is {result.returncode}")

    if not os.path.isfile(overlaps_output_embeddings_path):
        raise Exception(f"embedding file {overlaps_output_embeddings_path} should exist, but it does not exist")

def main(args):
    nda_input_path = get_full_path(args.nda_input_path) if args.nda_input_path != "-" else args.nda_input_path
    nda_output_path = get_full_path(args.nda_output_path) if args.nda_output_path != "-" else args.nda_output_path
    vecalign_dir = get_full_path(args.vecalign_dir)
    tmp_dir = args.tmp_dir
    nda_input_is_base64 = args.nda_input_is_base64
    src_lang = args.src_lang
    trg_lang = args.trg_lang
    vecalign_num_overlaps = args.vecalign_num_overlaps
    alignment_max_size = args.vecalign_alignment_max_size

    if (nda_input_path == "-" and nda_output_path == "-"):
        raise Exception("you can only pipe either nda input or nda output, not both of them")

    nda_src_sentences = f"{tmp_dir}/sentences.src"
    nda_trg_sentences = f"{tmp_dir}/sentences.trg"
    vecalign_overlaps_src_path = f"{tmp_dir}/overlaps.src"
    vecalign_overlaps_trg_path = f"{tmp_dir}/overlaps.trg"
    vecalign_overlaps_src_embeddings_path = f"{tmp_dir}/overlaps.emb.src"
    vecalign_overlaps_trg_embeddings_path = f"{tmp_dir}/overlaps.emb.trg"

    if (nda_input_path != "-" and not os.path.isfile(nda_input_path)):
        raise Exception(f"file {nda_output_path} must exist")
    if (nda_output_path != "-" and not os.path.isfile(nda_output_path)):
        raise Exception(f"file {nda_output_path} must exist")
    if not os.path.isdir(vecalign_dir):
        raise Exception(f"directory {vecalign_dir} must exist")
    if not os.path.isdir(tmp_dir):
        raise Exception(f"temporal directory does not exist: {tmp_dir}")

    # Check vecalign necessary files
    check_vecalign_files(vecalign_dir)

    # Process output from NDA
    src_sentences, trg_sentences = process_nda_output(nda_input_path, nda_output_path, nda_input_is_base64)

    # Store sentences
    with open(nda_src_sentences, "w") as file:
        file.write("\n".join(src_sentences) + "\n")
    with open(nda_trg_sentences, "w") as file:
        file.write("\n".join(trg_sentences) + "\n")

    # Generate overlapping files and embeddings
    vecalign_overlap(vecalign_dir, nda_src_sentences, vecalign_overlaps_src_path, vecalign_overlaps_src_embeddings_path, src_lang, vecalign_num_overlaps)
    vecalign_overlap(vecalign_dir, nda_trg_sentences, vecalign_overlaps_trg_path, vecalign_overlaps_trg_embeddings_path, trg_lang, vecalign_num_overlaps)

    # Execute vecalign
    result = subprocess.run([f"{vecalign_dir}/vecalign.py", "--alignment_max_size", str(alignment_max_size),
                             "--src", nda_src_sentences, "--tgt", nda_trg_sentences,
                             "--src_embed", vecalign_overlaps_src_path, vecalign_overlaps_src_embeddings_path,
                             "--tgt_embed", vecalign_overlaps_trg_path, vecalign_overlaps_trg_embeddings_path,
                            ])

    if result.returncode != 0:
        raise Exception(f"something went wrong while running vecalign: return code is {result.returncode}")

def parse_args():
    parser = argparse.ArgumentParser(description='NDA output process for Vecalign')

    # Embedding
    parser.add_argument('nda_input_path', metavar='nda-input-path',
                        help='Path to the input file of NDA. \'-\' for reading from stdin')
    parser.add_argument('nda_output_path', metavar='nda-output-path',
                        help='Path to the output file of NDA with the results. \'-\' for reading from stdin')
    parser.add_argument('vecalign_dir', metavar='vecalign-dir',
                        help='Path to vecalign directory')

    # Other options
    parser.add_argument('--src-lang', required=True,
                        help='Lang. of the src documents/sentences')
    parser.add_argument('--trg-lang', required=True,
                        help='Lang. of the trg documents/sentences')
    parser.add_argument('--tmp-dir', metavar='PATH', required=True,
                        help='Path to tmp directory')
    parser.add_argument('--nda-input-is-base64', action='store_true',
                        help='If the nda input file contains the first row with Base64 instead of paths to documents')

    # Vecalign specific options
    parser.add_argument('--vecalign-num-overlaps', type=int, default=4,
                        help='Number of overlaps to apply to every sentence when using Vecalign. The default value is 4')
    parser.add_argument('--vecalign-alignment-max-size', type=int, default=4,
                        help='Max. size for alignments when using Vecalign. The default value is 4')

    args = parser.parse_args()

    return args

def main_wrapper():
    args = parse_args()

    main(args)

if __name__ == "__main__":
    main_wrapper()
