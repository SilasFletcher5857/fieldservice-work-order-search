from fieldservice_search import SearchRequest, WorkOrderDocument, WorkOrderSearch


def test_leak_query_returns_active_water_damage_follow_up() -> None:
    vectors = {
        "water": [1.0, 0.0],
        "door": [0.0, 1.0],
        "leak query": [0.9, 0.1],
    }

    def deterministic_embedder(texts: list[str]) -> list[list[float]]:
        return [
            vectors[
                "leak query"
                if text == "active leak"
                else "water"
                if "Water staining" in text
                else "door"
            ]
            for text in texts
        ]

    search = WorkOrderSearch(deterministic_embedder)
    search.index(
        [
            WorkOrderDocument(
                work_order_id="WO-1042",
                photo_description="Water staining below the drain line",
                dispatch_status="on_site",
                technician_follow_up="Clear the line and confirm the ceiling is dry",
            ),
            WorkOrderDocument(
                work_order_id="WO-1043",
                photo_description="Door roller outside its track",
                dispatch_status="dispatched",
                technician_follow_up="Measure alignment before replacing the roller",
            ),
        ]
    )

    hit = search.search(SearchRequest(query="active leak", limit=1))[0]

    assert hit.work_order_id == "WO-1042"
    assert hit.dispatch_status == "on_site"
    assert hit.technician_follow_up == "Clear the line and confirm the ceiling is dry"
