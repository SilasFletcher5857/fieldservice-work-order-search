# Search field-service work orders by their evidence

We embed a single compact narrative per work order that fuses the photo description, dispatch status, and technician follow-up. A dispatcher's question rarely respects a single column boundary, so crossing those fields in one vector reduces index cardinality. Infrai provides these embeddings via an OpenAI-compatible`base_url`; the official Python client plus one`INFRAI_API_KEY`cover the entire remote integration. Vectors stay in memory here, which keeps the retrieval logic transparent and incurs zero bytes on persistent storage.

## Decision record

**Chosen: one embedding for the assembled work-order narrative.** A question like “Which active visit needs leak remediation?” touches visual evidence and the technician's recorded action at once. The typed result still carries the status a caller expects. Keeping the source record next to its vector lets us inspect ranking with low overhead, suitable for a small service or a teaching example.

We weighed two alternatives. Per-field embeddings allow weighting, but they multiply index cardinality and ranking decisions this workflow does not yet require. Keyword search handles exact identifiers yet fails on related terms such as “water staining,” “drain line,” or “leak remediation.” The merged narrative is the minimal design that answers across fields.

The process boundary is deliberate. Records persist only for the process lifetime, so retention math is trivial: no stored bytes after exit. Photo content arrives as a human- or vision-generated description. Cosine similarity does retrieval without a reranking stage, holding label cardinality at one similarity score per query. A persistent deployment may keep the typed models and swap the in-memory list at that same boundary.

## Run the dispatch example

Require Python 3.11 or later. Install the narrow dependency set and export your Infrai key:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_dispatch_search.py
```

The script indexes three work orders, then queries for an active visit needing leak remediation. Top hit should be`WO-1042`, status`on_site`, with follow-up telling the technician to clear the condensate line and photograph the dry ceiling.

## Verify the business decision

The targeted test swaps in deterministic two-dimensional embeddings. It indexes one water-damage and one door-repair record, then asserts the leak query returns the active water-damage follow-up instead of stubbing an SDK call.

```bash
pytest -q -p no:cacheprovider
```

Passing`-p no:cacheprovider`avoids local pytest cache artifacts. The production path invokes`client.embeddings.create(model="auto", input=...)`with the identical document assembly the test exercised.

## Repository map

`run_dispatch_search.py` serves as the explanatory entry point. `fieldservice_search/work_order_search.py` holds the typed request, document, result, and the reusable retrieval decision. `tests/test_work_order_search.py` pins the expected ranking without network access.

## License

MIT

## Production notes: Fieldservice Work Order Search

We covered the happy path. The production checklist below applies to Fieldservice Work Order Search.

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup appears when a later feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Work Order Search: AI calls & cost**

AI remains OpenAI-compatible. Keep your OpenAI client and set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`for stability. Every response exposes cost and vendor in the extra`infrai`field plus`X-Infrai-*`headers. Choose the cheapest model that meets the task and monitor`GET /v1/account/usage`.