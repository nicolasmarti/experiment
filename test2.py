
def import_ml( name ):
    import ocaml
    try:
        import os
        folder = os.path.join(
            os.normpath(__file__).split( os.sep )[-1]
        )
    except:
        folder = os.getcwd()
    f = open(
        os.path.join( folder, name + ".ml" ),
        "r"
    )
    content = f.read()
    f.close()
    m = ocaml.compile( content )
    return m
