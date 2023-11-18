# subsplease-dl
A downloader from subsplease using their xdcc irc protocol

To be honest I don't understand this stuff too much but it works and it doesn't require peer to peer and that's cool.

## Setup Dev
```bash
just setup
```
#### OR
```bash
poetry install
poetry run pre-commit install
```

## Install
```bash
just install
```
#### OR
```bash
poetry build
pipx install ./dist/`ls -t dist | head -n2 | grep whl`
```

## Usage
```bash
subsplease-dl --help
```
Search for anime to download (Must use the full japanese name)
```bash
subsplease-dl "no game no life" --resolution 1080p
```
You can most likely see way too anime listed now, in that case you should filter it by the bot
```bash
subsplease-dl "no game no life" --resolution 1080p --bot "ARUTHA-BATCH|1080p"
```
You may also specify the epsisodes
```bash
subsplease-dl "no game no life" --resolution 1080p --bot "ARUTHA-BATCH|1080p" -e 1,4,8-12
```
Finally start the download
```bash
subsplease-dl "no game no life" --resolution 1080p --bot "ARUTHA-BATCH|1080p" -e 1,4,8-12 --download
```

*__NOTE:__* Replace `subsplease-dl` with `poetry run subsplease-dl` or `just run` if you haven't installed `subsplease-dl`.