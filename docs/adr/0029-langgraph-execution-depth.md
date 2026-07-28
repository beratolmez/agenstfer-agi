# ADR-0029: LangGraph Execution Depth

- **Status:** Proposed — decision required
- **Date:** 28 July 2026
- **Blocks:** SB-5, SB-4 in `docs/REMEDIATION_ROADMAP.md`

## Context

The documents and the code disagree about how much of LangGraph is actually used.

`DOMAIN_CONTRACTS.md` stated that LangGraph uses PostgreSQL for checkpointing and that
approvals are handled with `interrupt_before`/`interrupt_after`. ADR-0016 says the same.
Neither is true (both statements were corrected in ADR-0028):

- The compiled graph is the **straight chain of the topological order**
  (`langgraph_runtime.py:79-83`). `add_conditional_edges` is never called anywhere in the
  repository.
- There are no interrupts. The approval node writes `status="awaiting_approval"` and returns;
  every subsequent node then early-returns and the graph runs to `END` doing nothing
  (`:96-97`, `:131-159`).
- The checkpointer is a `MemorySaver` constructed inside `_build_graph`, which runs in
  `__init__` — so it is rebuilt for every run and its checkpoints die with the engine object
  (`:70,85`). Resume is reconstructed from `WorkflowStepRun` rows, not from a checkpoint.
- Conditional branching is emulated by hand: each node executor decides whether it is active
  by checking `state_data["_active_edges"]`, and writes `status="skipped"` if not
  (`:114-129`).

Functionally the engine is equivalent to a `for` loop over the topological order. That is not
a criticism of its correctness — it works, and the evidence gate and approval semantics on
top of it are sound — but it means none of LangGraph's durability or branching guarantees are
in force, while the documentation implies they are.

The second engine compounds this. Engine choice is a hardcoded ID set
(`persistent_runtime.py:468-477`) and `builtin-` is a reserved prefix
(`main.py:2153-2159`), so a user-authored workflow can never reach the LangGraph engine and
always runs on the copy-pasted fallback loop.

## Options

**A. Stay shallow, and say so.** Keep the straight chain and DB-driven resume. Delete the
checkpointer, since it costs memory and implies a durability guarantee that does not exist.
Correct ADR-0016 and keep the fallback loop as the single engine, dropping the LangGraph
dependency or retaining it only as a graph representation.
*Cost:* low. *Consequence:* parallel branches and durable mid-node resume stay unavailable;
the product's orchestration story becomes "a validated DAG executor", which is honest and
adequate for the current 12-node workflow.

**B. Go deep.** Adopt `add_conditional_edges` for real branching, `interrupt_before` on the
approval node, and `AsyncPostgresSaver` so checkpoints survive a restart. Consolidate onto
one engine so user workflows get the same semantics.
*Cost:* high — the state shape needs reducers before parallel branches are safe
(`LangGraphWorkflowState` is a plain `TypedDict` with no `Annotated` merge behaviour,
`:27-37`), and the approval resume path has to move from DB reconstruction to checkpoint
resumption. *Consequence:* durable long-lived approvals, parallel agent execution, and the
architecture the documents already describe.

**C. Deep checkpointing only.** Add the PostgreSQL checkpointer and interrupts, keep the
chain topology. Buys durable pause/resume without the state-reducer work.
*Cost:* medium. *Consequence:* no parallelism, but approvals become genuinely durable.

## Recommendation

**C now, B when parallelism is actually needed.** The straight chain is not currently a
constraint — the built-in workflow has no parallel branches — but the missing durable
checkpoint is a real gap for a product whose approvals can sit for seven days. Option C closes
the honesty gap and the durability gap without paying for state reducers the workflow does not
yet use.

Option A is defensible and cheapest, but it forecloses SB-5 and would need revisiting as soon
as a customer workflow needs a parallel branch.

Whichever is chosen, **the engine selection must stop being a hardcoded ID set** (SB-4). It
should be driven by a property of the definition, so user workflows and built-in workflows
execute under the same semantics.

## Consequences of not deciding

The fallback loop and the LangGraph engine keep drifting — they already handle errors
differently, which is how the `step_id` defect (ADR-0028) survived in one and not the other.
