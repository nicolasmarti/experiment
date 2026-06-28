module Type = struct
  
  module T = struct
    type ty =      
      | TyInt: ty
      | TyFloat: ty
      | TyVar: string -> ty
      | TyTuple: ty list -> ty
      | TyList: ty -> ty
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

module Term = struct
  
  module T = struct
    type te =      
      | TeInt: int -> te
      | TeFloat: float -> te
      | TeTuple: te list -> te
      | TeList: te list -> te
    ;;
  end;;
  
  open T;;
  open Type;;
  open Type.T;;

  let rec type_infer (t: te): ty =
    match t with
    | TeInt _ -> TyInt
    | TeFloat _ -> TyFloat
    | TeTuple l -> TyTuple (List.map  type_infer l)
    | TeList ts -> TyList (type_infer (List.hd ts))
  ;;
  
end;;

