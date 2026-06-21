def pprint( *s ):
    import sys
    print( *s )
    sys.stdout.flush()

pprint("#################################")
pprint("### Start ###")

#### import ####

## OCaml

import ocaml

# ocaml packages you need
# allows to open modules in import_ml
ocaml.require("why3")

# not sure what is usefull
ocaml.require("llvm")
ocaml.require("llvm.analysis")
ocaml.require("llvm.executionengine")
ocaml.require("llvm.target")
ocaml.require("llvm.scalar_opts")
ocaml.require("llvm.all_backends")
ocaml.require("llvm.all_backends.shared")

ocaml.require("poussin")

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

## LLVM

import llvmlite.binding as llvm
from llvmlite import ir
from ctypes import CFUNCTYPE, c_double, c_double, cast, c_void_p, c_ulonglong, c_longlong, POINTER, cdll, c_int, c_char

# All these initializations are required for code generation!
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()  # yes, even this one

def create_execution_engine():
    """
    Create an ExecutionEngine suitable for JIT code generation on
    the host CPU.  The engine is reusable for an arbitrary number of
    modules.
    """
    # Create a target machine representing the host
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    # And an execution engine with an empty backing module
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    return engine

def compile_ir(engine, llvm_ir):
    """
    Compile the LLVM IR string with the given engine.
    The compiled module object is returned.
    """
    # Create a LLVM module object from the IR
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    # Now add the module and make sure it is ready for execution
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    return mod

try:
    module = ir.Module(name="experiment")
    engine = create_execution_engine()
    pprint( engine )
except Exception as e:
    import traceback
    pprint( traceback.format_exc() )
    #pprint( e )

#################

pprint("#################################")
pprint("# OCaml <-> Python #")

m = import_ml("test")
m2 = import_ml("test2")

pprint(m.height(
  m.Node(label=1, children=[m.Node(label=2, children=[])])))

pprint(m.of_list(["a", "b", "c"]))

m.f()

pprint( "init_llvm[OCaml]:", m.init_llvm() )

#################
pprint("#################################")
pprint("# C/FFI/LLVM <-> Python #")

# ctypes types
c_longlong_p = POINTER(c_longlong)

# LLVM types
int64_t = ir.IntType( 64 )
int64_ptr_t = int64_t.as_pointer()
int64_0 = ir.Constant( int64_t, 0 )
int64_1 = ir.Constant( int64_t, 1 )

## Some Python callback

storage = dict()

#### Set

@CFUNCTYPE(c_longlong, c_longlong, c_longlong)
def storage_set( k, v ):
    #pprint( k, type(k), v, type(v) )
    storage[ k ] = v
    return v
llvm.add_symbol( "storage_set", cast(storage_set, c_void_p).value )
pprint( "storage_set:", llvm.address_of_symbol("storage_set") )
# the external symbol
ext_storage_set_ty = ir.FunctionType(int64_t, (int64_t, int64_t))
ext_storage_set_fct = ir.Function(
    module,
    ext_storage_set_ty,
    name="storage_set"
)
## the llvm function
llvm_storage_set_ty = ir.FunctionType(int64_t, (int64_t, int64_t))
llvm_storage_set_fct = ir.Function(
    module,
    llvm_storage_set_ty,
    name="llvm_storage_set"
)
block = llvm_storage_set_fct.append_basic_block(name="entry")
builder = ir.IRBuilder(block)
a, b = llvm_storage_set_fct.args
result = builder.call(ext_storage_set_fct, (a, b), name="res")
builder.ret(result)
##
#pprint( str( module ) )
## compiling
compile_ir( engine, str(module) )
## calling
func_ptr = engine.get_function_address("llvm_storage_set")
pprint( "func_ptr:", func_ptr )
##
cfunc = CFUNCTYPE(c_longlong, c_longlong, c_longlong)(func_ptr)
#pprint( storage )
res = cfunc(5, 56)
#pprint( storage )
res = cfunc(1, 5)
pprint( storage )

#### Get

@CFUNCTYPE(c_longlong, c_longlong, c_longlong_p)
def storage_get( k, v_p ):    
    #pprint( k, type(k), v_p, type(v_p) )
    if k in storage:
        v_p[0] = c_longlong(storage[k])
        return 1
    else:
        return 0
llvm.add_symbol( "storage_get", cast(storage_get, c_void_p).value )
pprint( "storage_get:", llvm.address_of_symbol("storage_get") )
# the external symbol
ext_storage_get_ty = ir.FunctionType(int64_t, (int64_t, int64_ptr_t))
ext_storage_get_fct = ir.Function(
    module,
    ext_storage_get_ty,
    name="storage_get"
)
## the llvm function
llvm_storage_get_ty = ir.FunctionType(int64_t, (int64_t,))
llvm_storage_get_fct = ir.Function(
    module,
    llvm_storage_get_ty,
    name="llvm_storage_get"
)
block = llvm_storage_get_fct.append_basic_block(name="entry")
builder = ir.IRBuilder(block)
(a,) = llvm_storage_get_fct.args
ptr_v = builder.alloca( int64_t, name = "ptr_v" )
result = builder.call(ext_storage_get_fct, (a, ptr_v), name="res")
icmp = builder.icmp_unsigned( "==", result, int64_1, "icmp")

block2 = llvm_storage_get_fct.append_basic_block(name="found")
builder2 = ir.IRBuilder(block2)

block3 = llvm_storage_get_fct.append_basic_block(name="not_found")
builder3 = ir.IRBuilder(block3)

builder.cbranch( icmp, block2, block3 )

builder3.ret(result)

loaded_v = builder2.load( ptr_v )
builder2.ret( loaded_v )

##
#pprint( str( module ) )
## compiling
compile_ir( engine, str(module) )
## calling
func_ptr = engine.get_function_address("llvm_storage_get")
pprint( "func_ptr:", func_ptr )
##
cfunc = CFUNCTYPE(c_longlong, c_longlong)(func_ptr)
pprint( cfunc(5), cfunc(1), cfunc(0))

##########

pprint("#################################")
pprint("# C/FFI/Cuda <-> Python #")
### loading some libs

## some cuda kernel
llvm.load_library_permanently("sample.so")
exec_ptr = llvm.address_of_symbol("exec")
pprint( "exec:", exec_ptr )

# could be called in python
cexec = CFUNCTYPE(c_int, c_ulonglong)(exec_ptr)
import time
start_time = time.time()
cexec( 200 )
pprint( time.time() - start_time )

pprint("#################################")
pprint("# C/FFI/GC <-> Python #")
## non copying garbge collector
llvm.load_library_permanently("gc.so")
gc_init_ptr = llvm.address_of_symbol("gc_init")
pprint( "gc_init:", gc_init_ptr )

cinit = CFUNCTYPE(c_char, c_int)(gc_init_ptr)
import time
start_time = time.time()
cinit( 10 )
pprint( time.time() - start_time )

###

pprint("#################################")
pprint("# Ocaml <-> Python #")

h = import_ml("harrison")
pprint( dir( h )[:10] )
pprint( type( h.formula ) )
pprint( type( h.formula.Ftrue ) )

m2 = import_ml("test2")
class Type(m2.Type, m2.Type.T):
    pass
print("Type:", dir(Type))
print(
    Type.tysz(
        Type.TyTuple(
            [Type.TyVar("s1"),
             Type.TyVar("s2"),
             Type.TyList(Type.TyInt())
             ]
        )
    )
)

###

pprint("### Done ###")
