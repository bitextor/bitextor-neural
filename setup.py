#!/usr/bin/env python

import setuptools
import os, shutil

def copytree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d)
        else:
            shutil.copy(s, d)

def reqs_from_file(src):
    requirements = []
    with open(src) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("-r"):
                requirements.append(line)
            else:
                add_src = line.split(' ')[1]
                add_req = reqs_from_file(add_src)
                requirements.extend(add_req)
    return requirements

if __name__ == "__main__":

    with open("docs/README.md", "r") as fh:
        long_description = fh.read()

    requirements=[]
    wd = os.path.dirname(os.path.abspath(__file__))

    copytree("preprocess/moses", os.path.join(wd, "bitextor/data/moses"))
    requirements = reqs_from_file("requirements.txt")

    setuptools.setup(
        name="bitextor",
        version="8.1.0",
        install_requires=requirements,
        license="GNU General Public License v3.0",
        #author=,
        #author_email=,
        #maintainer=,
        #maintainer_email,
        description="Bitextor generates translation memories from multilingual websites",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/bitextor/bitextor",
        packages=["bitextor", "bitextor.utils"],
        #classifiers=[],
        #project_urls={},
        package_data={
            "bitextor": [
                "Snakefile",
                "utils/clean-corpus-n.perl",
                "vecalign/*",
                "LASER/*",
                "LASER/*/*",
                "LASER/*/*/*",
                "data/*",
            ]
        },
        entry_points={
            "console_scripts": [
                "bitextor = bitextor.bitextor_cli:main",
                "bitextor-full = bitextor.bitextor_cli:main_full"
            ]
        }
        )
