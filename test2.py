source = r"""
module Type = struct
  
  module T = struct
    type ty =
      
      | TyInt
      | TyFloat

      | TyVar of string
    
      | TyTuple of ty list
      | TyList of ty
    ;;
  end;;
  
  open T;;
  
  type ty_ctxt = (string, ty) Hashtbl.t;;

  let rec sum l = match l with
    | [] -> 0
    | h::t -> h + (sum t);;

  let rec tysz (t: ty) : int =
    match t with
    | TyInt -> 1
    | TyFloat -> 1
    | TyVar _ -> 1
    | TyTuple l -> 1 + sum (List.map tysz l)
    | TyList t -> 1 + tysz t
  ;;

end;;
"""

import ocaml

print("##############")
m = ocaml.compile(source)
class Type(m.Type, m.Type.T):
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
