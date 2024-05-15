# srcomdumpy

A cringe script to dump an entire leaderboard off speedrun.com into either a CSV or JSON file.

Might not work for you, don't care if it doesn't.

Originally made for Odyssic but when I was finished with it he went "nvm somebody else made one for me already don't need it anymore :)". Thanks for letting me know ahead of time, cunt.

Dependencies: Python 3, requests


## Usage

Type `./srcomdumpy.py -h` for help.

This, for example, is how to dump the GTA Chinatown Wars leaderboards as CSV into a file named "gtacw.csv":

```
./srcomdumpy.py -f CSV -o gtacw.csv 'https://www.speedrun.com/gtacw'
```


## License

[MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/)
