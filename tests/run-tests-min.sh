#!/bin/bash

DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

if [[ ! -z "$BITEXTOR_TESTS_DIR" ]]; then
  DIR="$BITEXTOR_TESTS_DIR"
fi

source "${DIR}/common.sh"

exit_program()
{
  >&2 echo "$1 [-w workdir] [-f force_command] [-j threads]"
  >&2 echo ""
  >&2 echo "Runs several tests to check Bitextor is working"
  >&2 echo ""
  >&2 echo "OPTIONS:"
  >&2 echo "  -w <workdir>            Working directory. By default: \$HOME"
  >&2 echo "  -f <force_command>      Options which will be provided to snakemake"
  >&2 echo "  -j <threads>            Threads to use when running the tests"
  exit 1
}

WORK="${HOME}"
WORK="${WORK/#\~/$HOME}" # Expand ~ to $HOME
FORCE=""
THREADS=1

while getopts "hf:w:j:" i; do
    case "$i" in
        h) exit_program "$(basename "$0")" ; break ;;
        w) WORK=${OPTARG};;
        f) FORCE="--${OPTARG}";;
        j) THREADS="${OPTARG}";;
        *) exit_program "$(basename "$0")" ; break ;;
    esac
done
shift $((OPTIND-1))

BITEXTOR="bitextor-neural"
BICLEANER="${WORK}/bicleaner-model"
FAILS="${WORK}/data/fails.log"
mkdir -p "${WORK}"
mkdir -p "${WORK}/reports"
mkdir -p "${BICLEANER}"
mkdir -p "${WORK}/data/warc"
mkdir -p "${WORK}/data/warc/clipped"
rm -f "$FAILS"
touch "$FAILS"

# Download necessary files
# WARCs
download_warc "${WORK}/data/warc/greenpeace.warc.gz" https://github.com/bitextor/bitextor-data/releases/download/bitextor-warc-v1.1/greenpeace.canada.warc.gz &
# Bicleaner models
download_bicleaner_model "en-fr" "${BICLEANER}" &
wait

# Preprocess
### WARC clipped
if [ ! -f "${WORK}/data/warc/clipped/greenpeaceaa.warc.gz" ]; then
    ${DIR}/split-warc.py -r 100 "${WORK}/data/warc/greenpeace.warc.gz" "${WORK}/data/warc/clipped/greenpeace" &
fi

wait

# Remove unnecessary clipped WARCs
ls "${WORK}/data/warc/clipped/" | grep -v "^greenpeaceaa[.]" | xargs -I{} rm "${WORK}/data/warc/clipped/{}"
# Rename and link
mv "${WORK}/data/warc/greenpeace.warc.gz" "${WORK}/data/warc/greenpeace.original.warc.gz"
ln -s "${WORK}/data/warc/clipped/greenpeaceaa.warc.gz" "${WORK}/data/warc/greenpeace.warc.gz"

# MT (id >= 10)
(
    ${BITEXTOR} ${FORCE} --notemp -j ${THREADS} \
        --config profiling=True permanentDir="${WORK}/permanent/bitextor-mt-output-en-fr" \
            dataDir="${WORK}/data/data-mt-en-fr" transientDir="${WORK}/transient-mt-en-fr" \
            warcs="['${WORK}/data/warc/greenpeace.warc.gz']" preprocessor="warc2text" shards=1 batches=512 lang1=en lang2=fr \
            documentAlignerThreshold="0.5" alignerCmd="bash ${DIR}/../bitextor/example/dummy-translate.sh" sentenceAligner="vecalign" \
            bicleaner="${BICLEANER}/en-fr/metadata.yaml" tmx=True \
        &> "${WORK}/reports/10-mt-en-fr.report"
    annotate_and_echo_info 10 "$?" "$(get_nolines ${WORK}/permanent/bitextor-mt-output-en-fr/en-fr.sent.gz)"
) &

wait

# Results
failed=$(cat "$FAILS" | wc -l)

echo "------------------------------------"
echo "           Fails Summary            "
echo "------------------------------------"
echo "status | test-id | exit code / desc."
cat "$FAILS"

exit "$failed"
