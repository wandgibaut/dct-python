import configparser
import io
import unittest
from contextlib import redirect_stdout

from dct import parser


class ParserTests(unittest.TestCase):
    def test_emit_bash_arrays(self):
        config = configparser.ConfigParser()
        config["signals"] = {"death_threshold": "3", "suicide_note": "false"}

        output = io.StringIO()
        with redirect_stdout(output):
            parser.emit_bash_arrays(config)

        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "declare -A signals",
                'signals[death_threshold]="3"',
                'signals[suicide_note]="false"',
            ],
        )


if __name__ == "__main__":
    unittest.main()
