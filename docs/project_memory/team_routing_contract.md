# Team Routing Contract

Route Health & Fitness Platform work by ownership and risk:

| Work | Primary owner | Required coordination |
| --- | --- | --- |
| Product intent, priority, consequential action | User | Architecture for technical framing |
| Milestone scope, cross-boundary contract, acceptance | Architecture | User when product direction changes |
| Facts, calculations, validation, persistence, APIs | Backend/data | Architecture for contract changes |
| Production Next.js product experience | Frontend | Backend for API truth; human QA for acceptance |
| Repo workflow, scripts, environment support | DevOps/tooling | Architecture for workflow-contract changes |
| Bounded implementation and validation | Codex | Architecture for acceptance/closeout |
| Final visible/browser acceptance | Human QA | Frontend/Architecture for defects and disposition |

Provider/AI output is never an authoritative product-fact owner. AI-written daily prose is paused indefinitely. Streamlit is legacy/developer-only rather than a primary UI lane. Linux is optional secondary validation/runtime/demo infrastructure rather than the canonical development owner.

The current milestone is recorded at the top of `current_state.md`; do not hard-code an old accepted commit or milestone in this routing contract.
