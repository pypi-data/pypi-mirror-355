# ISHNE to CSV Converter

A Python package and CLI to convert ISHNE Holter ECG files (.ISHNE) to CSV format with timestamped entries.

## ISHNE Format

| Description | Data Type | No. of Bytes |
|-------------|-----------|--------------|
| Size (in bytes) of variable-length block | long int | 4 |
| Size (in samples) of ECG | long int | 4 |
| Offset of variable-length block (from beginning of file) | long int | 4 |
| Offset of ECG block (from beginning of file) | long int | 4 |
| Version of the file | short int | 2 |
| Subject First Name | char[40] | 40 |
| Subject Last Name | char[40] | 40 |
| Subject ID | char[20] | 20 |
| Subject Sex (0: unknown, 1: male, 2: female) | short int | 2 |
| Race (0: unknown, 1: Caucasian, 2: Black, 3: Oriental, 4–9: Reserved) | short int | 2 |
| Date of Birth (day, month, year) | 3 × short int | 6 |
| Date of Recording (day, month, year) | 3 × short int | 6 |
| Date of Output File Creation (day, month, year) | 3 × short int | 6 |
| Start Time (hour [0–23], minute, second) | 3 × short int | 6 |
| Number of Stored Leads | short int | 2 |
| Lead Specification (see lead specification table) | 12 × short int | 24 |
| Lead Quality (see lead quality table) | 12 × short int | 24 |
| Amplitude Resolution (integer number of nV) | 12 × short int | 24 |
| Pacemaker Code (see description) | short int | 2 |
| Type of Recorder (analog or digital) | char[40] | 40 |
| Sampling Rate (in Hz) | short int | 2 |
| Proprietary Information (if any) | char[80] | 80 |
| Copyright & Restriction of Diffusion (if any) | char[80] | 80 |
| Reserved | char[88] | 88 |

For complete details of the ISHNE format, please refer to [The ISHNE Holter Standard Output File Format](https://www.amps-llc.com/uploads/2017-12-7/The_ISHNE_Format.pdf).

## Features

- Converts all leads with correct timestamp for each sample
- Timestamps are calculated using the start time and sampling rate
- Progress bar to track conversion of large datasets
- Metadata printed and saved in a readable JSON format (name, date, time, leads, etc.)
- CLI support for direct command-line use
- Output CSV includes `time` column as the first column (nanoseconds)

## Installation

Install from PyPI:

```bash
pip install ishne_to_csv
```

## Usage

### As a Python Module

```python
from ishne_to_csv import ishne_to_csv

# Basic usage
ishne_to_csv("ECG.ISHNE") # Save as ECG.csv

# With parameters
ishne_to_csv("ECG.ISHNE", output_file="example.csv", metadata_file="patient_1.json", verbose=True)
```

### CLI Usage

```bash
python -m ishne_to_csv <input_file> [-o <output_file>] [-m <metadata_file] [-q] 
```

## CLI Parameters

| Argument | Description |
|----------|-------------|
| `input_file` | Path to the input ISHNE file (required) |
| `--output, -o <file_path>` | Optional output file path (default: same as input file but with `.csv` format at last) |
| `--metadata, -m <file_path>` |  Saves Metadata to file in JSON (default: same as input file but with `.json` format at last ) |
| `--quiet, -q` | Suppress console output (default: False) |

## Change Log

### v1.1
- Removed datetime overflow bug 
- Added support to save metadata information

## License

MIT License