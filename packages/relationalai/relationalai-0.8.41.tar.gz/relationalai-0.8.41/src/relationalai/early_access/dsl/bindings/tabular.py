import dataclasses
from abc import abstractmethod
from enum import Enum
from io import StringIO
from typing import Optional, Any, TypeVar, Generic, Tuple

import pandas as pd

from relationalai.early_access.builder import define, where
from relationalai.early_access.builder.std.decimals import parse_decimal64, parse_decimal128
from relationalai.early_access.dsl.bindings.common import BindableAttribute, BindableTable, ConceptBinding, \
    RoleBinding, FilteringConceptBinding, ReferentConceptBinding, FilterBy
from relationalai.early_access.dsl.bindings.relations import AttributeView, TabularSource
from relationalai.early_access.dsl.orm.relationships import Role, Relationship
from relationalai.early_access.dsl.orm.types import Concept
from relationalai.early_access.dsl.snow.common import ColumnRef, ColumnMetadata, _map_rai_type, CsvColumnMetadata, \
    ForeignKey, TabularMetadata
from relationalai.early_access.dsl.utils import normalize
from relationalai.early_access.rel.rel_utils import DECIMAL64_SCALE, DECIMAL128_SCALE

import relationalai.early_access.builder as qb


#=
# Constants.
#=

DEFAULT_DECIMAL_SIZE = 64
DEFAULT_DECIMAL_SCALE = 8


#=
# Bindable classes and interfaces.
#=

class BindableColumn(BindableAttribute):
    _table: BindableTable
    _references_column: Optional[ColumnRef]
    _attr_relation: AttributeView

    def __init__(self, table: BindableTable, model):
        self._table = table
        self._model = model
        self._references_column = None

    def __call__(self, *args):
        if self._attr_relation is None:
            raise Exception(f'Attribute view for `{self.physical_name()}` not initialized')
        return self.relation()(*args)

    def identifies(self, entity_type: Concept, filter_by: Optional[FilterBy] = None):
        if isinstance(entity_type, Enum):
            raise ValueError(f'Cannot bind to Enum {entity_type}, use `references` instead')
        binding = ConceptBinding(column=self, entity_type=entity_type, filter_by=filter_by)
        self._model.binding(binding)

    def references(self, entity_type: Concept, filter_by: Optional[FilterBy] = None):
        binding = ReferentConceptBinding(column=self, entity_type=entity_type, filter_by=filter_by)
        self._model.binding(binding)

    def filters_subtype(self, sub_type: Concept, by_value: Any):
        binding = FilteringConceptBinding(column=self, entity_type=sub_type, has_value=by_value, filter_by=None)
        self._model.binding(binding)

    def binds(self, elm, filter_by: Optional[FilterBy] = None):
        if isinstance(elm, Relationship):
            # this binds to the last role in binary relations
            if elm._arity() > 2:
                raise ValueError(f'Expected binary or unary relationship, got arity {elm._arity()}')
            roles = elm._roles()
            role = roles[-1]
        elif isinstance(elm, Role):
            role = elm
        else:
            raise Exception(
                f'Expected ORM Relationship or Role, got {type(elm)} - QB Relationships cannot be used in bindings')
        binding = RoleBinding(role=role, column=self, filter_by=filter_by)
        self._model.binding(binding)

    @property
    def table(self):
        return self._table

    @property
    def references_column(self) -> Optional[ColumnRef]:
        return self._references_column

    @references_column.setter
    def references_column(self, ref: ColumnRef):
        self._references_column = ref

    @abstractmethod
    def physical_name(self) -> str:
        pass

    @abstractmethod
    def type(self) -> qb.Concept:
        pass

    def ref(self) -> ColumnRef:
        return ColumnRef(self._table.table_name, self.physical_name())

    def __repr__(self):
        return f"BindableColumn({self.table.physical_name()}.{self.physical_name()}, {self.type()})"


class BindableSnowflakeColumn(BindableColumn):
    _metadata: ColumnMetadata

    def __init__(self, metadata: ColumnMetadata, table: 'SnowflakeTable', model):
        super().__init__(table, model)
        self._metadata = metadata
        self._datatype = _map_rai_type(self._metadata)
        self._attr_relation = AttributeView(model, self)

    def relation(self) -> AttributeView:
        return self._attr_relation

    @property
    def metadata(self):
        return self._metadata

    def physical_name(self) -> str:
        return self._metadata.name

    def type(self) -> qb.Concept:
        return _map_rai_type(self._metadata)

    def decimal_scale(self):
        return self._metadata.numeric_scale

    def decimal_size(self):
        precision = self._metadata.numeric_precision
        if precision is not None:
            if 1 <= precision <= 18:
                return 64
            elif 18 < precision <= 38:
                return 128
            raise ValueError(f'Precision {precision} is not supported (max: 38)')
        return precision

    def __repr__(self):
        return f"Snowflake:{super().__repr__()}"


class BindableCsvColumn(BindableColumn):
    _metadata: CsvColumnMetadata
    _column_basic_type: str

    def __init__(self, metadata: CsvColumnMetadata, table: 'CsvTable', model):
        super().__init__(table, model)
        self._metadata = metadata
        self._column_basic_type = "Int64" if metadata.datatype._name == qb.Integer._name else "string"
        self._attr_relation = AttributeView(model, self)

    def relation(self) -> AttributeView:
        return self._attr_relation

    @property
    def metadata(self):
        return self._metadata

    def physical_name(self) -> str:
        return self._metadata.name

    def type(self) -> qb.Concept:
        return self._metadata.datatype

    def basic_type(self):
        return self._column_basic_type

    def decimal_scale(self) -> Optional[int]:
        if self.type() is qb.Decimal64:
            return DECIMAL64_SCALE
        elif self.type() is qb.Decimal128:
            return DECIMAL128_SCALE
        else:
            return None

    def decimal_size(self) -> Optional[int]:
        if self.type() is qb.Decimal64:
            return 64
        elif self.type() is qb.Decimal128:
            return 128
        else:
            return None

    def __repr__(self):
        return f"CSV:{super().__repr__()}"


T = TypeVar("T", bound=BindableColumn)
class AbstractBindableTable(BindableTable,  Generic[T]):
    _columns: dict[str, T] = dataclasses.field(default_factory=dict)
    _foreign_keys: set[ForeignKey]

    def __init__(self, name: str, foreign_keys: set[ForeignKey], model):
        super().__init__(name)
        self._foreign_keys = foreign_keys
        self._model = model
        self._relation = TabularSource(self._model, self)

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        if key in self._columns:
            return self._columns[key]
        raise AttributeError(f'Table "{self.table_name}" has no column named "{key}"')

    def foreign_key(self, *refs: Tuple[BindableColumn, BindableColumn]):
        source_columns = []
        target_columns = []

        for source, target in refs:
            source_columns.append(ColumnRef(source.table.table_name, source.physical_name()))
            target_columns.append(ColumnRef(target.table.table_name, target.physical_name()))

        source_col_names = "_".join(col.column for col in source_columns)
        target_col_names = "_".join(col.column for col in target_columns)

        fk_name = f"fk_{source_col_names}__to__{target_col_names}"

        fk = ForeignKey(fk_name, source_columns, target_columns)
        self._foreign_keys.add(fk)
        self._process_foreign_key(fk)

    def key_type(self) -> qb.Concept:
        return qb.Integer

    @abstractmethod
    def physical_name(self) -> str:
        pass

    def columns(self):
        return self._columns

    def _process_foreign_keys(self):
        for fk in self._foreign_keys:
            self._process_foreign_key(fk)

    def _process_foreign_key(self, fk):
        # TODO : this doesn't work for composite FKs
        for col in fk.source_columns:
            target_col = fk.target_columns[0]
            self._columns[col.column].references_column = target_col


class SnowflakeTable(AbstractBindableTable[BindableSnowflakeColumn]):

    def __init__(self, metadata: TabularMetadata, model):
        super().__init__(metadata.name, metadata.foreign_keys, model)
        self._columns = {col.name: BindableSnowflakeColumn(col, self, model) for col in metadata.columns}
        self._process_foreign_keys()
        # for now, initialize the QB table so graph index can be built
        self._initialize_qb_table(metadata.name)

    def _initialize_qb_table(self, name: str):
        from relationalai.early_access.builder.snowflake import Table as QBTable
        self._qb_table = QBTable(name)
        QBTable._used_sources.add(self._qb_table)

    def __str__(self):
        # returns the name of the table, as well as the columns and their types
        return self.table_name + ':\n' + '\n'.join(
            [f' {col.metadata.name} {col.metadata.datatype}' for _, col in self._columns.items()]
        ) + '\n' + '\n'.join(
            [f' {fk.source_columns} -> {fk.target_columns}' for fk in self._foreign_keys]
        )

    def physical_name(self):
        # physical relation name is always in the form of `{database}_{schema}_{table}
        return self.table_name.lower().replace('.', '_')


class CsvTable(AbstractBindableTable[BindableCsvColumn]):
    _basic_type_schema: dict[str, str]
    _csv_data: list[str]

    def __init__(self, name: str, schema: dict[str, qb.Concept], model):
        super().__init__(name, set(), model)
        self._csv_data = list()
        self._columns = {column_name: BindableCsvColumn(CsvColumnMetadata(column_name, column_type), self, model)
                         for column_name, column_type in schema.items()}
        self._basic_type_schema = {col.metadata.name: col.basic_type() for col in self._columns.values()}

    def __str__(self):
        # returns the name of the table, as well as the columns and their types
        return self.table_name + ':\n' + '\n'.join(
            [f' {col.metadata.name} {col.metadata.datatype}' for _, col in self._columns.items()]
        ) + '\n' + '\n'.join(
            [f' {fk.source_columns} -> {fk.target_columns}' for fk in self._foreign_keys]
        )

    @property
    def csv_data(self) -> list[str]:
        return self._csv_data

    def physical_name(self) -> str:
        return self.table_name.lower()

    def data(self, csv_data: str):
        self._csv_data.append(csv_data)
        CsvSourceModule.generate(self, pd.read_csv(StringIO(normalize(csv_data)), dtype=self._basic_type_schema))

class CsvSourceModule:

    @staticmethod
    def generate(table: CsvTable, data: pd.DataFrame):
        for index, row in data.iterrows():
            for column_name in data.columns:
                value = row[column_name]
                if pd.notna(value):
                    column = table.__getattr__(column_name)
                    column_type = column.type()
                    relation = column.relation()
                    if column_type._name == qb.Date._name:
                        CsvSourceModule._row_to_date_value_rule(relation, index, value)
                    elif column_type._name == qb.DateTime._name:
                        CsvSourceModule._row_to_date_time_value_rule(relation, index, value)
                    elif column_type._name == qb.Decimal64._name:
                        CsvSourceModule._row_to_decimal64_value_rule(relation, index, value)
                    elif column_type._name == qb.Decimal128._name:
                        CsvSourceModule._row_to_decimal128_value_rule(relation, index, value)
                    else:
                        CsvSourceModule._row_to_value_rule(relation, index, value)

    @staticmethod
    def _row_to_value_rule(relation: AttributeView, row, value):
        define(relation(row, value))

    @staticmethod
    def _row_to_date_value_rule(relation: AttributeView, row, value):
        parse_date = qb.Relationship.builtins['parse_date']
        rez = qb.Date.ref()
        where(parse_date(value, 'Y-m-d', rez)).define(relation(row, rez))

    @staticmethod
    def _row_to_date_time_value_rule(relation: AttributeView, row, value):
        parse_datetime = qb.Relationship.builtins['parse_datetime']
        rez = qb.DateTime.ref()
        where(parse_datetime(value, 'Y-m-d HH:MM:SS z', rez)).define(relation(row, rez))

    @staticmethod
    def _row_to_decimal64_value_rule(relation: AttributeView, row, value):
        define(relation(row, parse_decimal64(value)))

    @staticmethod
    def _row_to_decimal128_value_rule(relation: AttributeView, row, value):
        define(relation(row, parse_decimal128(value)))
