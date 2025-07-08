"""
finance_engine
==============

Pure‑Python calculation engine for the MVNO scenario model.
Keeps Streamlit UI and maths separate so the logic can be
unit‑tested and reused in Excel or Jupyter.

Public surface
--------------
run_model(**overrides) -> (pd.DataFrame, dict)
load_defaults()        -> dict
save_defaults(dict)    -> None
"""
from .core import run_model
from .assumptions import load_defaults, save_defaults

__all__ = ["run_model", "load_defaults", "save_defaults"]
__version__ = "0.1.0"
