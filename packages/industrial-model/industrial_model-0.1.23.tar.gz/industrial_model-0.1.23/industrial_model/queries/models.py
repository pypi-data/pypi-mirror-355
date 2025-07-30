from typing import Any

from industrial_model.models import RootModel, TAggregatedViewInstance, TViewInstance
from industrial_model.statements import (
    AggregateTypes,
    AggregationStatement,
    SearchStatement,
    Statement,
    aggregate,
)

from .params import NestedQueryParam, QueryParam, SortParam


class BaseQuery(RootModel):
    def to_statement(self, entity: type[TViewInstance]) -> Statement[TViewInstance]:
        statement = Statement(entity)

        for key, item in self.__class__.model_fields.items():
            values = getattr(self, key)
            if not values:
                continue
            for metadata_item in item.metadata:
                if isinstance(metadata_item, SortParam):
                    statement.sort(values, metadata_item.direction)
                elif isinstance(metadata_item, QueryParam | NestedQueryParam):
                    statement.where(metadata_item.to_expression(values))

        return statement


class BasePaginatedQuery(BaseQuery):
    limit: int = 1000
    cursor: str | None = None

    def to_statement(self, entity: type[TViewInstance]) -> Statement[TViewInstance]:
        statement = super().to_statement(entity)
        statement.limit(self.limit)
        statement.cursor(self.cursor)

        return statement


class BaseSearchQuery(RootModel):
    query: str | None = None
    query_properties: list[str] | list[Any] | None = None
    limit: int = 1000

    def to_statement(
        self, entity: type[TViewInstance]
    ) -> SearchStatement[TViewInstance]:
        statement = SearchStatement(entity)

        for key, item in self.__class__.model_fields.items():
            values = getattr(self, key)
            if not values:
                continue
            for metadata_item in item.metadata:
                if isinstance(metadata_item, SortParam):
                    statement.sort(values, metadata_item.direction)
                elif isinstance(metadata_item, QueryParam | NestedQueryParam):
                    statement.where(metadata_item.to_expression(values))
        if self.query:
            statement.query_by(self.query, self.query_properties)
        statement.limit(self.limit)

        return statement


class BaseAggregationQuery(RootModel):
    aggregate: AggregateTypes | None = None
    group_by_properties: list[str] | list[Any] | None = None
    aggregation_property: str | None = None
    limit: int | None = None

    def to_statement(
        self, entity: type[TAggregatedViewInstance]
    ) -> AggregationStatement[TAggregatedViewInstance]:
        statement = aggregate(entity, self.aggregate)

        for key, item in self.__class__.model_fields.items():
            values = getattr(self, key)
            if not values:
                continue
            for metadata_item in item.metadata:
                if isinstance(metadata_item, QueryParam | NestedQueryParam):
                    statement.where(metadata_item.to_expression(values))

        if self.group_by_properties:
            statement.group_by(*self.group_by_properties)

        if self.aggregation_property:
            statement.aggregate_by(self.aggregation_property)

        if self.limit:
            statement.limit(self.limit)

        return statement
