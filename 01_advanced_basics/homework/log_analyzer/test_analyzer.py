import unittest
import sys
from log_analyzer import get_config


class TestAnalyzer(unittest.TestCase):
    def test_config_parser(self):
        sys.argv.append('--config=not_existed_config.ini')
        with self.assertRaises(FileNotFoundError):
            get_config(
                {'foo': 'bar'}
            )


if __name__ == "__main__":
    unittest.main()
