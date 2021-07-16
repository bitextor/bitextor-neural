# Bitextor installation

### Download Bitextor's submodules

```bash
# if you are cloning from scratch:
git clone --recurse-submodules https://github.com/bitextor/bitextor.git

# otherwise:
git submodule update --init --recursive
```

### Required packages

These are some external tools that need to be in the path before installing the project. If you are using an apt-like package manager you can run the following commands line to install all these dependencies:

```bash
# mandatory:
sudo apt install python3 python3-venv python3-pip golang-go build-essential cmake libboost-all-dev liblzma-dev time curl pigz parallel

# optional, feel free to skip dependencies for components that you don't expect to use:
## wget crawler:
sudo apt install wget
## warc2text:
sudo apt install uchardet libuchardet-dev libzip-dev
## biroamer:
sudo apt install libgoogle-perftools-dev libsparsehash-dev
## Heritrix, PDFExtract and boilerpipe:
sudo apt install openjdk-8-jdk
## PDFExtract:
## PDFExtract also requires protobuf installed for CLD3 (installation instructions below)
sudo apt install autoconf automake libtool ant maven poppler-utils apt-transport-https ca-certificates gnupg software-properties-common
```

### C++ dependencies

Compile and install Bitextor's C++ dependencies:

```bash
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$HOME/.local ..
# other prefix can be used, as long as it is in the PATH
make -j install
```

Optionally, it is possible to skip the compilation of the dependencies that are not expected to be used:

```bash
cmake -DSKIP_MGIZA=ON -DCMAKE_INSTALL_PREFIX=$HOME/.local .. # MGIZA is used for dictionary generation
# other dependencies that can optionally be skipped:
# WARC2TEXT, DOCALIGN, BLEUALIGN, HUNALIGN, BIROAMER, KENLM
```

### Golang packages

Additionally, Bitextor uses [giashard](https://github.com/paracrawl/giashard) for WARC files preprocessing.

```bash
# build and place the necessary tools in $HOME/go/bin
go get github.com/paracrawl/giashard/...
```

### Pip dependencies

Furthermore, most of the scripts in Bitextor are written in Python 3. The minimum requirement is Python>=3.7.

Some additional Python libraries are required. They can be installed automatically with `pip`. We recommend using a virtual environment to manage Bitextor installation.

```bash
# create virtual environment & activate
python3 -m venv /path/to/virtual/environment
source /path/to/virtual/environment/bin/activate

# install dependencies in virtual enviroment
pip3 install --upgrade pip
# bitextor:
pip3 install .
# additional dependencies:
pip3 install ./bicleaner && pip install ./kenlm --install-option="--max_order 7"
pip3 install ./bifixer
pip3 install ./biroamer && python3 -m spacy download en_core_web_sm
```

If you don't want to install all Python requirements in `requirements.txt` because you don't expect to run some of Bitextor modules, you can comment those `*.txt` in `requirements.txt` and rerun Bitextor installation.

