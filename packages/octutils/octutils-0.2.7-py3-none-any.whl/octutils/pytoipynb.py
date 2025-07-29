import jupytext

notebook = jupytext.read(f"functions.py")
jupytext.write(notebook, f"functions.ipynb", fmt='.ipynb')