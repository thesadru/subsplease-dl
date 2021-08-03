# subsplease-dl
A downloader from subsplease using their xdcc irc protocol

To be honest I don't understand this stuff too much but it works and it doesn't require peer to peer and that's cool.

# usage
```
python main.py --help
```
Search for anime to download (Must use the full japanese name)
```
python main.py "no game no life" --resolution 1080p
```
You can most likely see way too anime listed now, in that case you should filter it by the bot
```
python main.py "no game no life" --resolution 1080p --bot "ARUTHA-BATCH|1080p"
```
You may also specify the epsisodes
```
python main.py "no game no life" --resolution 1080p --bot "ARUTHA-BATCH|1080p" -e 1,4,8-12
```
Finally start the download
```
python main.py "no game no life" --resolution 1080p --bot "ARUTHA-BATCH|1080p" -e 1,4,8-12 --download
```