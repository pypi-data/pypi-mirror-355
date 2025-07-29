import os
import logging

class FileSplitter:
    def __init__(self, file_path, lines_per_file=1000, output_dir="output", file_prefix="split_part"):
        """
        Initializes FileSplitter with required parameters.
        :param file_path: Path to the input file
        :param lines_per_file: Number of lines per split file
        :param output_dir: Directory to store split files
        :param file_prefix: Prefix for output files
        """
        self.file_path = file_path
        self.lines_per_file = lines_per_file
        self.output_dir = output_dir
        self.file_prefix = file_prefix

        # Set up logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

        # Validate file
        if not os.path.exists(self.file_path):
            logging.error(f"File not found: {self.file_path}")
            raise FileNotFoundError(f"File not found: {self.file_path}")

        if not os.path.isfile(self.file_path):
            logging.error(f"Invalid file path: {self.file_path}")
            raise ValueError(f"Invalid file path: {self.file_path}")

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def split(self):
        """
        Efficiently splits the file into multiple smaller files based on lines_per_file.
        """
        try:
            file_count = 1
            line_count = 0
            output_file = None

            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                for line in infile:
                    if line_count % self.lines_per_file == 0:
                        if output_file:
                            output_file.close()
                        output_file_path = os.path.join(self.output_dir, f"{self.file_prefix}_{file_count}.txt")
                        output_file = open(output_file_path, 'w', encoding='utf-8')
                        file_count += 1
                    output_file.write(line)
                    line_count += 1

                if output_file:
                    output_file.close()

            logging.info(f"✅ File splitting complete! {file_count - 1} files created in '{self.output_dir}'")

        except Exception as e:
            logging.error(f"❌ Error occurred: {e}")
            raise
