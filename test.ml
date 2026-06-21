(*************)

open Format;;

type 'a tree = Node of { label : 'a; children : 'a tree list }

let rec height (Node { label = _; children }) =
  1 + List.fold_left (fun accu tree -> max accu (height tree)) 0 children

let rec of_list nodes =
  match nodes with
  | [] -> invalid_arg "of_list"
  | [last] -> Node { label = last; children = [] }
  | hd :: tl -> Node { label = hd; children = [of_list tl] }

(*************)

open Why3;;

let f() =
  
  let fmla_true : Term.term = Term.t_true in
  let fmla_false : Term.term = Term.t_false in
  let fmla1 : Term.term = Term.t_or fmla_true fmla_false in
  printf "@[formula 1 is:@ %a@]@." Pretty.print_term fmla1;
  
  let prop_var_A : Term.lsymbol =
    Term.create_psymbol (Ident.id_fresh "A") [] in
  let prop_var_B : Term.lsymbol =
    Term.create_psymbol (Ident.id_fresh "B") [] in
  let atom_A : Term.term = Term.ps_app prop_var_A [] in
  let atom_B : Term.term = Term.ps_app prop_var_B [] in
  let fmla2 : Term.term =
    Term.t_implies (Term.t_and atom_A atom_B) atom_A in
  printf "@[formula 2 is:@ %a@]@." Pretty.print_term fmla2;
  
  (* building the task for formula 1 alone *)
  let task1 : Task.task = None in
  let goal_id1 : Decl.prsymbol = Decl.create_prsymbol (Ident.id_fresh "goal1") in
  let task1 : Task.task = Task.add_prop_decl task1 Decl.Pgoal goal_id1 fmla1 in
  printf "@[task 1 is:@\n%a@]@." Pretty.print_task task1;
  
  (* task for formula 2 *)
  let task2 = None in
  let task2 = Task.add_param_decl task2 prop_var_A in
  let task2 = Task.add_param_decl task2 prop_var_B in
  let goal_id2 = Decl.create_prsymbol (Ident.id_fresh "goal2") in
  let task2 = Task.add_prop_decl task2 Decl.Pgoal goal_id2 fmla2 in
  printf "@[task 2 created:@\n%a@]@." Pretty.print_task task2;
  
  (* reads the default config file *)
  let config : Whyconf.config = Whyconf.init_config None in
  (* the [main] section of the config file *)
  let main : Whyconf.main = Whyconf.get_main config in
  (* all the provers detected, from the config file *)
  let provers : Whyconf.config_prover Whyconf.Mprover.t =
    Whyconf.get_provers config in
  (* default resource limits *)
  let limits =
    Call_provers.{empty_limits with
                   limit_time = Whyconf.timelimit main;
                   limit_mem = Whyconf.memlimit main } in
  (* One prover named Alt-Ergo in the config file *)
  let alt_ergo : Whyconf.config_prover =
    let fp = Whyconf.parse_filter_prover "Alt-Ergo" in
    (* all provers that have the name "Alt-Ergo" *)
    let provers = Whyconf.filter_provers config fp in
    if Whyconf.Mprover.is_empty provers then begin
        eprintf "Prover Alt-Ergo not installed or not configured@.";
        exit 1
      end else begin
        printf "Versions of Alt-Ergo found:";
        Whyconf.(Mprover.iter (fun k _ -> printf " %s" k.prover_version) provers);
        printf "@.";
        (* returning an arbitrary one *)
        snd (Whyconf.Mprover.max_binding provers)
      end in
  (* Specific version 2.5.4 of Alt-Ergo in the config file *)
  let _ : Whyconf.config_prover =
    let fp = Whyconf.parse_filter_prover "Alt-Ergo,2.5.4" in
    let provers = Whyconf.filter_provers config fp in
    if Whyconf.Mprover.is_empty provers then begin
        eprintf "Prover Alt-Ergo 2.5.4 not installed or not configured, using version %s instead@."
          Whyconf.(alt_ergo.prover.prover_version) ;
        alt_ergo (* we don't want to fail this time *)
      end else
      snd (Whyconf.Mprover.max_binding provers) in
  (* builds the environment from the [loadpath] *)
  let env : Env.env = Env.create_env (Whyconf.loadpath main) in
  (* loading the Alt-Ergo driver *)
  let alt_ergo_driver : Driver.driver =
    try
      Driver.load_driver_for_prover main env alt_ergo
    with e ->
      eprintf "Failed to load driver for alt-ergo: %a@."
        Exn_printer.exn_printer e;
      exit 1 in
  
  (* calls Alt-Ergo *)
  let result1 : Call_provers.prover_result =
  Call_provers.wait_on_call
    (Driver.prove_task
       ~limits
       ~config:main
       ~command:alt_ergo.Whyconf.command
       alt_ergo_driver
       task1) in
  let result2 : Call_provers.prover_result =
  Call_provers.wait_on_call
    (Driver.prove_task
       ~command:alt_ergo.Whyconf.command
       ~config:main
       ~limits:{ limits with Call_provers.limit_time = 10. }
       alt_ergo_driver
       task2) in
  
  (* prints Alt-Ergo answer *)
  printf "@[On task 1, Alt-Ergo answers %a@]@."
    (Call_provers.print_prover_result ?json:None) result1;
  printf "@[On task 2, Alt-Ergo answers %a@]@."
    (Call_provers.print_prover_result ?json:None) result2;;


(*************)

open Llvm;;
open Llvm_executionengine;;
open Llvm_target;;
open Llvm_scalar_opts;;
open Llvm_all_backends;;

let init_llvm() =
  printf "Initialized OCaml LLVM\n";
  Llvm_all_backends.initialize()

(*************)
