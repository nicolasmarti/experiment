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

  let f1 (s: string): ty = TyVar(s);;

end;;
