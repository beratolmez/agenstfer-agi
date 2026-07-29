# Task packet — T13, T14, T15: make workflow templates loadable

Packet format: [`AI_DEVELOPMENT_GUIDE.md`](../AI_DEVELOPMENT_GUIDE.md) §8. Read the floor
(guide §1) before starting. Task type: **frontend + backend bug fix** — guide §3 says read the
failing reproduction first, then only the modules involved. Do not read the architecture set
for this.

These three are one packet because they share a single reproduction and none of them is
independently observable: fixing the backend without the error handling still shows the user
nothing, and fixing the error handling without the backend just makes the failure visible.

---

```
Goal          : Loading any workflow template and pressing "Doğrula" shows a truthful
                validation result instead of failing silently.

Files         : apps/api/agi_server/main.py:2393-2395
                apps/api/agi_server/workflow/templates.py:210-212
                apps/web/src/features/workflow/WorkflowEditor.tsx:300, 418-423
                apps/api/tests/test_workflow_templates.py
                apps/web/src/features/workflow/WorkflowEditor.test.tsx

Change        : T13 — GET /api/workflows/templates serves the raw dicts from
                     list_workflow_templates(), which have no `version`, so the editor
                     posts a body the API rejects with 422. Serve canonical definitions
                     instead. REUSE template_to_workflow_definition() in templates.py:160 —
                     it already sets version=1 and is verified to convert all five templates
                     without loss. Convert EVERY template, not only the executable ones.

                T14 — validate() at WorkflowEditor.tsx:418 is the only editor action with no
                     error handling. Give it the same try/catch/setActionError shape its four
                     siblings already use; copy dryRun() at line 440 rather than inventing a
                     pattern.

                T15 — the validation indicator is initialised to its own success string
                     (useState("Geçerli graph"), line 300). Start it in a neutral state that
                     cannot be mistaken for a passed check, e.g. "Doğrulanmadı".

Out of scope  : Do NOT use get_executable_templates() — it filters out the catalog template
                and the picker must keep showing all five.
                Do NOT change the validator, the template contents, or the node catalogue.
                Do NOT fix T16/T17/T18 (the api.ts type, the duplicate selector labels, the
                missing accessible names). They are real and they are separate packets.
                Do NOT touch the workflow selector, save, publish or run paths.
                Do NOT rename the Turkish UI strings beyond the one in T15.

Verification  : uv run python -c "
                import sys; sys.path.insert(0,'apps/api')
                from agi_server.workflow.models import WorkflowDefinition
                from agi_server.main import workflow_templates_list
                print([WorkflowDefinition.model_validate(t).version
                       for t in workflow_templates_list()['items']])"

                Expected after the fix: [1, 1, 1, 1, 1]
                Today it raises: ValidationError: 1 validation error for WorkflowDefinition
                (this calls the endpoint function directly -- no HTTP, no session, no
                running stack; /api/workflows/templates itself requires authentication,
                so plain curl returns auth.required rather than the payload)

                Then the whole gate:
                ./scripts/project-check.sh          # or scripts\project-check.ps1
                Expected: exit 0, backend and frontend suites green.

Done when     : In the browser at #workflow, with the network tab open:
                1. Şablon Yükle -> "Lead Discovery & Signal Enrichment" -> Doğrula
                   POST /api/workflows/validate returns 200 and the footer reads
                   "Geçerli graph".
                2. Şablon Yükle -> "Enterprise Account Expansion Blueprint" -> Doğrula
                   returns 200 with valid=false and the footer reads
                   "3 doğrulama hatası".
                3. Before pressing Doğrula the footer does NOT read "Geçerli graph".
                Step 2 is the one that matters: it proves the error path and the indicator
                are both real. A change that only satisfies step 1 has not fixed T15.
```

---

## Reproduction (observed 29 July 2026, before any fix)

1. `#workflow` → **Şablon Yükle** → any template.
2. **Doğrula** → `POST /api/workflows/validate` → **422**, nothing appears on screen.
3. **Kaydet** → `PUT /api/workflows/{id}/draft` → **422**, generic "İstek doğrulanamadı".

The 422 body names the cause exactly:

```json
{"type":"missing","loc":["body","version"],"msg":"Field required"}
```

A persisted workflow (`growth-diagnostic v2`) validates **200**, which is what scopes this to
templates rather than to the editor as a whole.

## Why the tests did not catch it

`get_executable_templates()` and `get_catalog_templates()` are called only from
`test_workflow_templates.py`. No production path calls either. The endpoint that *is* served
calls `list_workflow_templates()`, which nothing tests. The suite is green over a broken
feature — so **adding a regression test is part of this packet, not optional**:

- Backend: assert every item from `GET /api/workflows/templates` parses as a
  `WorkflowDefinition`. Today that fails; per guide §5 requirement 3, confirm it fails against
  the unfixed code before you fix it.
- Frontend: assert that a rejected validate call surfaces an error rather than being
  swallowed.

## Facts already established — do not re-derive

- All five templates convert through `template_to_workflow_definition()` with node and edge
  counts preserved (9/8, 9/8, 9/8, 9/8, 1/0).
- After conversion the four executable templates validate with **0 issues**; the catalog
  template `enterprise-expansion-blueprint` is invalid with **3 issues** (`trigger.count`,
  `output.missing`, `approval.count`). Both outcomes are correct and are what the Done-when
  steps expect.
- The template picker renders only `name`, `nodes.length` and `edges.length`
  (`WorkflowEditor.tsx:507-511`), so dropping `category`, `description` and `type` from the
  response changes nothing the user sees.

## Reporting back

State which of the three Done-when steps you observed, in a browser, and paste the network
status for each. If you could not run the stack, say so — guide §5: an honest "I could not
test this" is worth more than a confident claim that turns out to be wrong.
