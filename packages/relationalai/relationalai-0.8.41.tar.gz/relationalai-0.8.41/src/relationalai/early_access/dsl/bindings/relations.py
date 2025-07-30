from relationalai.early_access.dsl.orm.relations import AssertedRelation
from relationalai.early_access.dsl.bindings.common import BindableAttribute, BindableTable

import relationalai.early_access.builder as qb


class AttributeView(AssertedRelation):
    """
    A class representing an attribute view relation.
    """

    def __init__(self, model, attr: BindableAttribute):
        name = self._get_relation_name(attr)
        sig = self._get_relation_signature(attr)
        super().__init__(model, name, *sig)
        self._attr = attr

    @staticmethod
    def _get_relation_name(attr: BindableAttribute):
        """
        Returns the relation name of the attribute view, combining table name and attribute name.
        """
        attr_name = attr.physical_name()
        table_name = attr.table.physical_name()
        name = f"{table_name}:{attr_name}"
        return name

    @staticmethod
    def _get_relation_signature(attr: BindableAttribute):
        """
        Returns the relation signature of the attribute view.
        """
        sig = (attr.table.key_type(), attr.type())
        return sig

    def attr(self):
        """
        Returns the attribute of the attribute view.
        """
        return self._attr

    def __repr__(self):
        return f"AttributeView({self.qualified_name()})"


class TabularSource:
    """
    A class representing a tabular source relation. Currently, all it does is
    generates a `Rel` declare statement for the source relation, so that there are
    no compilation issues in case the source relation is empty (no data loaded).
    """

    def __init__(self, model, source: BindableTable):
        self._name = source.physical_name()
        self._model = model
        self._generate_body()

    def _generate_body(self):
        src = f"declare {self._name}"
        self._model.qb_model().define(qb.RawSource('rel', src))
