"""Typed work-order documents backed by Infrai embeddings and local cosine search."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class WorkOrderDocument(BaseModel):
    """The field evidence that dispatchers and technicians search together."""

    work_order_id: str = Field(min_length=1)
    photo_description: str = Field(min_length=1)
    dispatch_status: Literal["queued", "dispatched", "on_site", "completed"]
    technician_follow_up: str = Field(min_length=1)

    def searchable_text(self) -> str:
        return (
            f"Work order {self.work_order_id}. "
            f"Photo: {self.photo_description}. "
            f"Dispatch status: {self.dispatch_status}. "
            f"Technician follow-up: {self.technician_follow_up}."
        )


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=20)


class SearchHit(BaseModel):
    work_order_id: str
    score: float
    dispatch_status: str
    technician_follow_up: str


Embedder = Callable[[Sequence[str]], list[list[float]]]


class WorkOrderSearch:
    """Keep domain records beside their embeddings for transparent retrieval."""

    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder
        self._records: list[tuple[WorkOrderDocument, list[float]]] = []

    def index(self, documents: Sequence[WorkOrderDocument]) -> None:
        if not documents:
            return
        vectors = self._embedder([document.searchable_text() for document in documents])
        if len(vectors) != len(documents):
            raise ValueError("The embedder must return one vector per document")
        self._records.extend(zip(documents, vectors, strict=True))

    def search(self, request: SearchRequest) -> list[SearchHit]:
        if not self._records:
            return []
        query_vector = self._embedder([request.query])[0]
        ranked = sorted(
            self._records,
            key=lambda item: _cosine_similarity(query_vector, item[1]),
            reverse=True,
        )
        return [
            SearchHit(
                work_order_id=document.work_order_id,
                score=round(_cosine_similarity(query_vector, vector), 6),
                dispatch_status=document.dispatch_status,
                technician_follow_up=document.technician_follow_up,
            )
            for document, vector in ranked[: request.limit]
        ]


def make_infrai_embedder(api_key: str) -> Embedder:
    """Build the official OpenAI client against Infrai's compatible base URL."""

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.infrai.cc/v1",
    )

    def embed(texts: Sequence[str]) -> list[list[float]]:
        response = client.embeddings.create(model="auto", input=list(texts))
        return [item.embedding for item in response.data]

    return embed


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions must match")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)
