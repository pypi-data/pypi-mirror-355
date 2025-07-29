# file-splitter-harsh

A Python library to efficiently split large text files into smaller chunks and perfect for preprocessing large datasets, logs, or CSV files.

---

## Installation

Install using pip:

```bash
pip install file-splitter-harsh


## Example
from filesplitter.splitter import FileSplitter

# Initialize the splitter
splitter = FileSplitter(
    file_path="large_file.txt",     # Path to the input file
    lines_per_file=1000,            # Number of lines per output file
    output_dir="output",            # Directory to save split files
    file_prefix="chunk"             # Prefix for output file names
)

# Start splitting the file
splitter.split()

| Parameter        | Type | Default        | Description                                     |
| ---------------- | ---- | -------------- | ----------------------------------------------- |
| `file_path`      | str  | Required       | Path to the input file                          |
| `lines_per_file` | int  | `1000`         | Number of lines each output file should contain |
| `output_dir`     | str  | `"output"`     | Directory where output files will be saved      |
| `file_prefix`    | str  | `"split_part"` | Prefix to use for each generated file name      |

#Example Output
If your input file has 2500 lines and lines_per_file=1000, you'll get:
output/
-chunk_1.txt  (1000 lines)
-chunk_2.txt  (1000 lines)
-chunk_3.txt  (500 lines)

Logging Example
2025-06-12 10:00:00 - INFO - File splitting complete! 3 files created in 'output'
