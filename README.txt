# Live Captions Companion UI redesign

Replace `gui/main_window.py` with the included file.

This update preserves the existing MainWindow methods and capture/export/history
logic while reorganizing the interface into:
- a branded header with capture state indicator,
- a session-library sidebar,
- a transcript workspace with clearer editing actions.

After replacing the file, run:

```powershell
python -m py_compile gui/main_window.py
python -m unittest discover -s tests -v
python main.py
```

This patch uses Qt styles and standard widgets; it adds no new dependencies.
