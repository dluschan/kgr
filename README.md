# kgr
Multitool for converting data from [memopzk.org](https://memopzk.org) to Google Maps

## Description
This project provides a tool for converting data from the format used on memopzk.org to a format supported by Google Maps.

## Installation
You can install kgr using pip:
```sh
pip install kgr
```

## Contribution
We welcome contributions from the community! Please create pull requests and report bugs via the Issues system.

## License
This project is licensed under the MIT license. For details, see the LICENSE file.

## Requirements
 - Python 3
 - Dependencies specified in `project.toml`

## Usage Examples
View the program version:
```sh
python -m kgr -v
```

View the help:
```sh
python -m kgr -h
python -m kgr prepare -h
python -m kgr geocode -h
python -m kgr convert -h
python -m kgr check -h
```

Complete Data Processing Workflow:
```sh
python -m kgr prepare -i list__76cce2b204_25-05-2024.csv -y -v -e errors.txt
...after filling in the city field...
python -m kgr geocode -i list__76cce2b204_25-05-2024.csv -y -r -v -e missing.txt
python -m kgr convert -i list__76cce2b204_25-05-2024.csv -s "Список политзаключённых — Мемориал."
```

## Common Options for All Commands
All commands that process input files use the -i option for specifying the input file. To specify the output file, use the -o option or overwrite the input file with -y. When reading input data from a CSV file, the program will try to determine the delimiter character itself, but you can specify it explicitly using the -d option. Similarly, you can specify the encoding of the input file using the -c option, with the default being UTF-8 encoding. The prepare and geocode commands make requests for the necessary information and can take considerable time. To see progress during their execution, you can add the -v or -vv option. If a request cannot be processed, the program will display failed requests, which can be redirected to a file using the -e option. Additionally, each command has its own specific options.

## Command Descriptions
### Prepare CSV files from [memopzk.org](https://memopzk.org)
```sh
usage: __main__.py prepare [-h] -i INPUT (-y | -o OUTPUT) [-d DELIMITER] [-c ENCODING] [-v] [-q | -e ERROR]

Parse source csv file from https://memopzk.org

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        input csv file with data
  -y, --replace         replace input csv file
  -o OUTPUT, --output OUTPUT
                        output csv file
  -d DELIMITER, --delimiter DELIMITER
                        delimiter in the input csv file
  -c ENCODING, --encoding ENCODING
                        encoding of the input csv file
  -v, --verbosity       add progress messages
  -q, --quiet           ignore errors
  -e ERROR, --error ERROR
                        log file for errors
```

### Get Geocodes from OpenStreetMap
```sh
usage: __main__.py geocode [-h] -i INPUT (-y | -o OUTPUT) [-r] [-d DELIMITER] [-c ENCODING] [-v] [-q | -e ERROR]

Get geocode from OpenStreetMap

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        input csv file with data
  -y, --replace         replace input csv file
  -o OUTPUT, --output OUTPUT
                        output csv file
  -r, --random          randomize geocode for exclude collision
  -d DELIMITER, --delimiter DELIMITER
                        delimiter in the input csv file
  -c ENCODING, --encoding ENCODING
                        encoding of the input csv file
  -v, --verbosity       add progress messages
  -q, --quiet           ignore get geocode errors
  -e ERROR, --error ERROR
                        log file for missing persons
```

### Convert CSV File to KML
```sh
usage: __main__.py convert [-h] -i INPUT [-o OUTPUT] [-d DELIMITER] [-c ENCODING] [-s SUFFIX] [-l LAYOUT]

Convertor data from CSV to KML

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        input csv file with data
  -o OUTPUT, --output OUTPUT
                        output kml file
  -d DELIMITER, --delimiter DELIMITER
                        delimiter in the input csv file
  -c ENCODING, --encoding ENCODING
                        encoding of the input csv file
  -s SUFFIX, --suffix SUFFIX
                        the phrase added to the description of each person
  -l LAYOUT, --layout LAYOUT
                        the internal name of the xml document and the name of the layer on the map
```

### Get Single Address Geocode
```sh
usage: __main__.py check [-h] -a ADDRESS

Check get geocode for single address

options:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        input address for check
```
