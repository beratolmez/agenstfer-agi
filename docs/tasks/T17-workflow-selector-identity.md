# Task packet — T17: the workflow selector must say which workflow you are editing

Packet format: [`AI_DEVELOPMENT_GUIDE.md`](../AI_DEVELOPMENT_GUIDE.md) §8. Read the floor
(guide §1) before starting. Task type: **frontend** — guide §3: `docs/API_REFERENCE.md`, then
`docs/WORKFLOW_AUTHORING.md`, which describes this editor and this defect.

> **Prerequisite — the environment must have an admin account.** At the time of writing the
> installation had zero users and `setup_completed: false`, so the console lands on the
> bootstrap screen and the editor is unreachable. Someone with the bootstrap token has to
> create the first admin before this packet can be verified. **If you reach the bootstrap
> screen, stop and report it — do not create accounts, and do not modify the database.**

---

## Why this matters more than it looks

The editor picks the execution engine by workflow id
(`workflow/persistent_runtime.py`, see `docs/WORKFLOW_AUTHORING.md`): `growth-diagnostic` and
`builtin-growth-diagnostic` run on LangGraph, anything else runs on the fallback runtime. Both
of those render in the selector as the identical string "Growth Diagnostic".

So a user cannot tell which workflow they are editing, and therefore cannot tell which engine
will run it. This is a correctness problem wearing a cosmetic disguise.

---

```
Goal          : The selector shows which workflow is loaded, and never shows a
                different workflow from the one on the canvas.

Files         : apps/web/src/features/workflow/WorkflowEditor.tsx:491-502
                apps/web/src/features/workflow/WorkflowEditor.test.tsx

Change        : (a) Options render only `item.name` (line 501), and two workflows share
                    the name "Growth Diagnostic". Include something that distinguishes
                    them. WorkflowSummary already carries `id`, `version` and `status`
                    (apps/web/src/types.ts:111-118) -- no API change is needed. Prefer
                    the id, since the id is what selects the engine.

                (b) The select is `value={workflow?.id}` over `workflowOptions`, which
                    is built from the saved catalogue (line 491). Loading a template
                    sets an id that is not in that list, and a select whose value
                    matches no option displays its first option instead -- so the
                    selector claims one workflow while the canvas holds another.
                    Represent the unsaved-template state explicitly rather than letting
                    it fall through: an option for the loaded-but-unsaved definition, or
                    a disabled placeholder. The canvas and the selector must agree at
                    all times.

Out of scope  : Do NOT fix T18 (sidebar and template-picker buttons with no accessible
                name). Separate packet, adjacent code.
                Do NOT change the engine-selection rule, the workflow API, the
                WorkflowSummary shape, or openWorkflow's loading logic.
                Do NOT rename workflows to make them distinguishable -- the names are
                data, the presentation is the defect.
                Do NOT restyle the toolbar.

                Environment: do not create accounts, change passwords, modify database
                rows, rebuild or recreate containers, or edit configuration. If the
                stack is not usable, stop and report it.

Environment   : docker compose -f docker-compose.yml -f docker-compose.cloud.yml up -d
                The console is at http://localhost:8080, the editor at #workflow.
                Do not use the base topology alone.

Verification  : npm --prefix apps/web test
                ./scripts/project-check.sh          # or scripts\project-check.ps1
                Expected: exit 0.

                Add a frontend test that fails against the current component: assert
                that two workflows sharing a name produce distinguishable option labels.
                Run it against the unchanged component first and confirm it fails.

Done when     : In a browser at #workflow, with the page loaded:
                1. The selector's two entries are distinguishable, and the one shown as
                   selected is the workflow named in the footer.
                2. After Şablon Yükle -> any template, the selector does NOT show a
                   different workflow than the footer's id. State what it shows instead.
                3. Reload the page; the selector still agrees with the footer.

                Evidence required for each of the three: paste the accessibility tree or
                DOM text of the select element and the footer, taken from the loaded
                page -- not the JSX, and not a description. If you cannot open a
                browser, say so and stop; do not substitute HTTP requests or reason
                about the strings from source.
```

---

## Facts already established — do not re-derive

- `workflowOptions` (line 491) already de-duplicates by id, so `growth-diagnostic` appearing
  twice in `GET /api/workflows` (one draft, one published row) is not the cause.
- The select carries `aria-label="Workflow seçimi"`, so it is reachable by accessible name.
  The missing-name problem is T18 and affects other buttons.
- `WorkflowSummary` = `{ id, version, name, status, created_at, updated_at }`. Everything
  needed to disambiguate is already on the client.

**Verification status of the reproduction:** derived from the component source, **not observed
in a browser** — the environment had no admin account when this packet was written, so the
editor could not be reached. Sub-problem (b) in particular is inferred from how a `<select>`
behaves when its `value` matches no option. Confirm both behaviours in the browser before you
change anything, and say in your report whether what you saw matched this description. If it
did not, the packet is wrong and that is worth more than the fix.

## Reporting back

Give the three done-when observations with their evidence, whether the new frontend test was
run against both versions of the component, and the gate's exit code. Say explicitly whether
the reproduction matched the description above. Guide §5: an honest "I could not test this" is
worth more than a confident claim that turns out to be wrong.
