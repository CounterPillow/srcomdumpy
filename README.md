# srcomdumpy

A cringe script to dump an entire leaderboard off speedrun.com into either a CSV or JSON file.

Might not work for you, don't care if it doesn't.

Originally made for Odyssic but when I was finished with it he went "nvm somebody else made one for me already don't need it anymore :)". Thanks for letting me know ahead of time, cunt.

Dependencies: Tested with Python 3.6 or newer, urllib3 1.22 or newer.


## Usage

Type `./srcomdumpy.py -h` for help.

This, for example, is how to dump the GTA Chinatown Wars leaderboards as CSV into a file named "gtacw.csv":

```
./srcomdumpy.py -f CSV -o gtacw.csv 'https://www.speedrun.com/gtacw'
```

If no `-o`/`--output` parameter is given, the script will output to the standard output. This means that on Unix-like systems, you can easily pipe the output to another application. In this example, the Celeste leaderboards are downloaded in the (default) JSON format and piped into gzip for compression, which then redirects it to the file `celeste.json.gz`:

```
./srcomdumpy.py 'https://www.speedrun.com/celeste' | gzip --best > celeste.json.gz
```


## Limitations

Due to speedrun.com v1 API limitations, it's only possible to retrieve up to 10000 elements per query. The script splits up the queries by category and run status, and asks for sorted results which it then iterates ascending and descending. This means that in practice, a category with more than 20000 verified runs (or 20k rejected runs, or 20k new runs) cannot be fetched in its entirety. The script will warn if this occurred.


## License

[MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/)
