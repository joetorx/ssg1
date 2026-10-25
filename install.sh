#!/usr/bin/env bash

# Copyright (c) 2026 Joel Torres
# Licensed under the MIT License. See the file LICENSE for details.

home_bin="$HOME/bin"
ssg1_home="$HOME/.ssg1"
ssg1_venv="$ssg1_home/.venv"

mkdir -p "$home_bin"
mkdir -p "$ssg1_home"

if [ ! -d "$ssg1_venv" ]; then
    echo "=> Creating python venv at $ssg1_venv"
    python3 -m venv "$ssg1_venv"
fi

source $ssg1_venv/bin/activate
if [ $? == 0 ]; then
    #pip install --upgrade pip
    pip3 --disable-pip-version-check --quiet install -r requirements.txt
fi

echo "=> Copying files to $home_bin and $ssg1_home"
cp bin/* $home_bin
cp ssg1.py $ssg1_home/ssg1.py
cp -r assets $ssg1_home

chmod +x $home_bin/ssg1*
chmod +x $ssg1_home/ssg1.py
