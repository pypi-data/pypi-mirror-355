import os
import unittest
from filesplitter import FileSplitter


class TestFileSplitter(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_data.txt"
        self.output_dir = "test_output"
        with open(self.test_file, "w") as f:
            for i in range(1, 101):
                f.write(f"Line {i}\n")

    def test_split_file(self):
        splitter = FileSplitter(self.test_file, lines_per_file=10, output_dir=self.output_dir)
        splitter.split()

        # Verify that 10 files were created
        output_files = os.listdir(self.output_dir)
        self.assertEqual(len(output_files), 10)

    def tearDown(self):
        os.remove(self.test_file)
        for file in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, file))
        os.rmdir(self.output_dir)


if __name__ == "__main__":
    unittest.main()
