# Application paths test fix

Replace `tests/test_paths.py` in the project with the file in this patch.

No change to `capture/paths.py` is required. The test now mocks the `os` reference
used by `capture.paths` rather than patching the shared `os.name` attribute,
which inadvertently changes how `pathlib.Path` behaves on Windows.

Run:

```powershell
python -m unittest tests.test_paths -v
python -m unittest discover -s tests -v
```
