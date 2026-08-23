"""Index three work orders, then retrieve the record needing a leak follow-up."""

import os

from fieldservice_search import SearchRequest, WorkOrderDocument, WorkOrderSearch
from fieldservice_search.work_order_search import make_infrai_embedder


def main() -> None:
    search = WorkOrderSearch(make_infrai_embedder(os.environ["INFRAI_API_KEY"]))
    search.index(
        [
            WorkOrderDocument(
                work_order_id="WO-1042",
                photo_description="Water staining below the rooftop air-handler drain line",
                dispatch_status="on_site",
                technician_follow_up="Clear the condensate line and photograph the dry ceiling",
            ),
            WorkOrderDocument(
                work_order_id="WO-1043",
                photo_description="Loading dock door resting above the floor on its left side",
                dispatch_status="dispatched",
                technician_follow_up="Measure the track alignment before replacing the roller",
            ),
            WorkOrderDocument(
                work_order_id="WO-1044",
                photo_description="Lobby thermostat displaying a low-battery symbol",
                dispatch_status="completed",
                technician_follow_up="Battery replaced and temperature verified with facilities",
            ),
        ]
    )

    hits = search.search(SearchRequest(query="Which active visit needs leak remediation?", limit=1))
    for hit in hits:
        print(hit.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
