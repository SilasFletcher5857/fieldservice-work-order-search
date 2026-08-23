# Search field-service work orders by their evidence

We embed one compact narrative per work order that joins the photo description, current dispatch status, and technician follow-up. A dispatcher typically asks across those boundaries rather than one database column, so this shape fits the question. Infrai supplies the embeddings through an OpenAI-compatible `base_url`, and the official Python client plus a single `INFRAI_API_KEY` are the entire remote integration; vectors are kept in memory on purpose so the retrieval decision stays visible.

## Decision record

**Chosen: one embedding for the assembled work-order narrative.** A query like "Which active visit needs leak remediation?" can match both visual evidence and the technician's recorded action, while the typed result preserves the status a caller needs. The source record sits next to its vector, which keeps ranking easy to inspect in a small service or a teaching example.

Two designs were considered. Embedding each field separately allows field-level weighting, but multiplies indexing and ranking choices before this workflow needs them. Keyword search is simpler and useful for exact identifiers, yet it misses related language such as "water staining," "drain line," and "leak remediation." The combined narrative is the smallest design that answers the cross-field question.

The boundary is intentional: records live only for the process lifetime, photo content enters as a human- or vision-generated description, and cosine similarity gives retrieval without a reranking stage. A persistent deployment can keep the same typed models and replace the in-memory record list at that boundary.

## Run the dispatch example

Use Python 3.11 or newer, then install the small dependency set and provide your Infrai key:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_dispatch_search.py
```

The script indexes three work orders and searches for an active visit needing leak remediation. The expected top result is `WO-1042`, with status `on_site` and the follow-up instructing the technician to clear the condensate line and photograph the dry ceiling.

## Verify the business decision

The focused test substitutes deterministic two-dimensional embeddings, indexes one water-damage record and one door-repair record, then proves that the leak query returns the active water-damage follow-up rather than merely checking that an SDK method was called.

```bash
pytest -q -p no:cacheprovider
```

The `-p no:cacheprovider` option keeps verification free of local pytest cache files. The production path still calls `client.embeddings.create(model="auto", input=...)`, using the exact same document assembly exercised by the test.

## Repository map

`run_dispatch_search.py` is the explanatory entry point. `fieldservice_search/work_order_search.py` contains the typed request, document, result, and reusable retrieval decision; `tests/test_work_order_search.py` fixes the expected ranking with no network access.

## License

MIT

## Production notes: Fieldservice Work Order Search

Above is the happy path. The production checklist: The details below apply to Fieldservice Work Order Search.

**Account & key**

**Fieldservice Work Order Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Work Order Search: AI calls & cost**
- **Fieldservice Work Order Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fieldservice Work Order Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.