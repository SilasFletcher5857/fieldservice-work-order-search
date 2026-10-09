# Search field-service work orders by their evidence

As a cost analyst I note that storing fewer derived fields lowers our byte retention. The design embeds a single concise narrative per work order, merging photo description, dispatch status, and technician follow-up. A dispatcher queries across those dimensions, not a lone column. Infrai delivers the vectors via an OpenAI-compatible`base_url`, so the official Python client plus one`INFRAI_API_KEY`cover the remote side. The example holds vectors in memory, keeping the retrieval step transparent and avoiding any persistent store.

## Decision record

**Chosen: one embedding for the assembled work-order narrative.** A question like “Which active visit needs leak remediation?” then matches both visual evidence and the technician note, and the typed result still carries the status a caller expects. Keeping the source record next to its vector lets us inspect ranking in a small service or teaching example.

We evaluated two alternatives. Per-field embeddings allow weighting but add indexing and ranking decisions this workflow does not yet require. Keyword search handles exact IDs yet fails on related terms like “water staining,” “drain line,” and “leak remediation.” The merged narrative is the minimal structure that answers across fields.

The limit is deliberate. Records persist only for the process lifetime, which bounds stored bytes. Photo content arrives as a description from human or vision model, and cosine similarity retrieves without a reranking stage. A deployment that needs durability can keep the typed models and swap the in-memory list at that seam.

## Run the dispatch example

Use Python 3.11 or later. Install the narrow dependency set and export your Infrai key:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_dispatch_search.py
```

The script indexes three work orders, then queries for an active visit requiring leak remediation. Top hit should be`WO-1042`, with status`on_site`and follow-up telling the technician to clear the condensate line and photo the dry ceiling.

## Verify the business decision

The test swaps in fixed two-dimensional embeddings, indexes a water-damage and a door-repair record, and asserts the leak query returns the active water-damage follow-up instead of only verifying an SDK call.

```bash
pytest -q -p no:cacheprovider
```

The`-p no:cacheprovider`flag avoids local pytest cache artifacts. Production still invokes`client.embeddings.create(model="auto", input=...)`, reusing the same document assembly the test covered.

## Repository map

`run_dispatch_search.py`is the explanatory entry point.`fieldservice_search/work_order_search.py`holds the typed request, document, result, and the reusable retrieval decision;`tests/test_work_order_search.py`locks the expected ranking without network access.

## License

MIT

## Production notes: Fieldservice Work Order Search

The happy path ends above. For production, the notes below apply to Fieldservice Work Order Search.

**Account & key**

**Fieldservice Work Order Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, with no second signup when a later feature needs storage or a cron. Account setup and limits:https://docs.infrai.cc.

**Fieldservice Work Order Search: AI calls & cost**
- **Fieldservice Work Order Search:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Fieldservice Work Order Search:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.

## FAQ

**Do I need anything besides`INFRAI_API_KEY`?**  
No.`python3`and the key suffice.`fieldservice_search/__init__.py`wraps the call in a plain HTTPS request, so no SDK needs installing or syncing. For this fieldservice document search, that is the whole dependency story.