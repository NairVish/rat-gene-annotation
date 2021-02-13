# Rat Gene Annotation Script

## Requirements

* Python 3.6+
* Beautiful Soup 4 (`pip install beautifulsoup4`)

## Execution

This script takes in 4 parameters:

* `-i`/`--input`: Input file (for an example, see `anno_sample.csv`).
* `-o`/`--output`: Desired name/location of the output file.
* `-k`/`--api_key`: Entrez Programming Utilities (E-utilities) API key.
    * Follow the instructions [here](https://www.ncbi.nlm.nih.gov/books/NBK25497/) (under the header *"Coming in December 2018: API Keys"*) to get one.
* `-c`/`max_count` (OPTIONAL): The maximum number of rows to read from the input file. If this option is not given, then the script will read *all* rows.

### Sample Commands

```
python ./main.py -i ./anno_sample.csv -o ./output.csv -k myapikey12345
```

Or with the max count parameter:

```
python ./main.py -i ./anno_sample.csv -o ./output.csv -k myapikey12345 -c 100
```