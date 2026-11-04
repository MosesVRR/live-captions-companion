import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from capture.paths import get_app_data_dir, get_transcripts_dir


class TestApplicationPaths(unittest.TestCase):
    def test_non_windows_data_directory_uses_xdg_data_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mocked_os = SimpleNamespace(name="posix", environ=os.environ)
            with patch("capture.paths.os", mocked_os), patch.dict(
                os.environ, {"XDG_DATA_HOME": temp_dir}, clear=False
            ):
                self.assertEqual(
                    get_app_data_dir(),
                    Path(temp_dir) / "live-captions-companion",
                )

    def test_transcripts_directory_is_inside_app_data_directory(self):
        with patch("capture.paths.get_app_data_dir") as get_app_dir:
            get_app_dir.return_value = Path("/tmp/app-data")
            with patch("capture.paths.Path.cwd", return_value=Path("/tmp/no-legacy")):
                with patch("capture.paths.os.name", "nt"):
                    with patch.dict(os.environ, {"LOCALAPPDATA": "/tmp/local"}, clear=False):
                        self.assertEqual(
                            get_transcripts_dir(), Path("/tmp/app-data/transcripts")
                        )


if __name__ == "__main__":
    unittest.main()
