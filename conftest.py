# Empty on purpose: its presence at the repo root makes pytest add this
# directory to sys.path during collection, so `import bank` / `import cli`
# resolve regardless of whether tests are run as `pytest` or
# `python -m pytest` (the latter already adds cwd to sys.path on its own,
# which is why this gap wasn't caught locally the first time).
