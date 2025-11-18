class TestDictList(object):

    def __init__(self):

        return

    def __getattribute__( self, name ):

        print( name, type(name) )
        
        print( "getattribute:", name )
    
        return

    def __getitem__( self, idx ):
        
        print( "getitem:", idx )

        

T = TestDictList()

print( 2 in T )

T.doudou
