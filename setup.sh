# Python
python -m venv .venv
source .venv/bin/activate
pip install llvmlite 


# Ocaml
opam switch create . 4.14.2
eval $(opam env)
opam install -y ocaml-in-python llvm why3

#
pip install ./_opam/lib/ocaml-in-python
cp _opam/lib/ocaml-in-python/ocaml/ocaml_in_python.so .venv/lib/python3.10/site-packages/ocaml/
