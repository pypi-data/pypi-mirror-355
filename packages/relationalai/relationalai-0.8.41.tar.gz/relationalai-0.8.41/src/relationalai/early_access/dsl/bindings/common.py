import dataclasses
from abc import abstractmethod
from enum import Enum
from typing import Any, Optional, Union

import relationalai.early_access.builder as qb
from relationalai.early_access.dsl.orm.relationships import Role
from relationalai.early_access.dsl.snow.common import ColumnRef

import datetime


PrimitiveFilterBy = Union[int, float, str, bool, datetime.date, datetime.datetime, Enum]
FilterBy = Union[PrimitiveFilterBy, qb.Expression, tuple[qb.Expression]]


class BindableTable:
    """
    A class representing a bindable table.
    """

    _table_name: str

    def __init__(self, name: str):
        self._table_name = name

    @property
    def table_name(self):
        return self._table_name

    @abstractmethod
    def key_type(self) -> qb.Concept:
        pass

    @abstractmethod
    def physical_name(self) -> str:
        pass


class BindableAttribute:

    @property
    @abstractmethod
    def table(self) -> BindableTable:
        pass

    @abstractmethod
    def physical_name(self) -> str:
        pass

    @abstractmethod
    def type(self) -> qb.Concept:
        pass

    @property
    @abstractmethod
    def references_column(self) -> Optional[ColumnRef]:
        pass

    @abstractmethod
    def ref(self) -> ColumnRef:
        pass

    @abstractmethod
    def decimal_scale(self) -> Optional[int]:
        pass

    @abstractmethod
    def decimal_size(self) -> Optional[int]:
        pass

    @abstractmethod
    def relation(self) -> qb.Relationship:
        pass


@dataclasses.dataclass(frozen=True)
class Binding:
    column: BindableAttribute
    filter_by: Optional[FilterBy]


@dataclasses.dataclass(frozen=True)
class RoleBinding(Binding):
    role: Role

    def __str__(self):
        return f'RoleBinding[{self.column.table.physical_name()}:{self.column.physical_name()} -> {self.role.player().name()}]'


@dataclasses.dataclass(frozen=True)
class AbstractConceptBinding(Binding):
    """
    Represents a parent class for all concept bindings.
    """
    entity_type: qb.Concept


@dataclasses.dataclass(frozen=True)
class ConceptBinding(AbstractConceptBinding):
    """
    Represents a binding between an identifier column and a specific entity type.

    This binding could either represent a constructor binding (instances of the entity type are constructed from the
    values), referent binding (instances of the entity type are being looked up by the values), or a subtype binding
    (instances are being looked up using the parent type's ref scheme, or it acts as a constructor for the subtype).

    The binding later gets classified by the reasoner into either an IdentifierBinding or a SubtypeBinding.
    """

    def __str__(self):
        return f'ConceptBinding[{self.column.table.physical_name()}:{self.column.physical_name()} -> {self.entity_type.name()}]'


@dataclasses.dataclass(frozen=True)
class ReferentConceptBinding(AbstractConceptBinding):
    """
    Represents a binding between an identifier column and a specific entity type, where the values in the column
    are used to look up existing instances of the entity type.
    """

    def __str__(self):
        return f'ReferentConceptBinding[{self.column.table.physical_name()}:{self.column.physical_name()} -> {self.entity_type.name()}]'


@dataclasses.dataclass(frozen=True)
class FilteringConceptBinding(AbstractConceptBinding):
    has_value: Any

    def __str__(self):
        return f'FilteringSubtypeBinding[{self.column.table.physical_name()}:{self.column.physical_name()} == {self.has_value}]'
