from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from itertools import chain
from typing import List, NamedTuple, Callable

import numpy as np

from AnyQt.QtWidgets import QSizePolicy, QStyle, \
    QButtonGroup, QRadioButton, QComboBox
from AnyQt.QtCore import Qt

from Orange.data import Variable, Table, ContinuousVariable, TimeVariable
from Orange.data.util import get_unique_names
from Orange.widgets import gui, widget
from Orange.widgets.settings import (
    ContextSetting, Setting, DomainContextHandler
)
from Orange.widgets.utils.signals import AttributeList
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import Input, Output
from Orange.widgets.utils.itemmodels import DomainModel


class OpDesc(NamedTuple):
    name: str
    func: Callable[[np.ndarray], np.ndarray]
    time_preserving: bool = False


class OWAggregateColumns(widget.OWWidget):
    name = _tr.m[215, "Aggregate Columns"]
    description = _tr.m[216, "Compute a sum, max, min ... of selected columns."]
    category = _tr.m[217, "Transform"]
    icon = "icons/AggregateColumns.svg"
    priority = 1200
    keywords = _tr.m[218, "aggregate columns, aggregate, sum, product, max, min, mean, median, variance"]

    class Inputs:
        data = Input(_tr.m[219, "Data"], Table, default=True)
        features = Input(_tr.m[220, "Features"], AttributeList)

    class Outputs:
        data = Output(_tr.m[221, "Data"], Table)

    class Warning(widget.OWWidget.Warning):
        discrete_features = widget.Msg(_tr.m[222, "Some input features are categorical:\n{}"])
        missing_features = widget.Msg(_tr.m[223, "Some input features are missing:\n{}"])

    want_main_area = False

    Operations = {_tr.m[224, "Sum"]: OpDesc(_tr.m[225, "Sum"], np.nansum),
                  _tr.m[226, "Product"]: OpDesc(_tr.m[227, "Product"], np.nanprod),
                  "Min": OpDesc(_tr.m[228, "Minimal value"], np.nanmin, True),
                  "Max": OpDesc(_tr.m[229, "Maximal value"], np.nanmax, True),
                  "Mean": OpDesc(_tr.m[230, "Mean value"], np.nanmean, True),
                  _tr.m[231, "Variance"]: OpDesc(_tr.m[232, "Variance"], np.nanvar),
                  _tr.m[233, "Median"]: OpDesc(_tr.m[234, "Median"], np.nanmedian, True)}
    KeyFromDesc = {op.name: key for key, op in Operations.items()}

    SelectAll, SelectAllAndMeta, InputFeatures, SelectManually = range(4)

    settingsHandler = DomainContextHandler()
    variables: List[Variable] = ContextSetting([])
    selection_method: int = Setting(SelectManually, schema_only=True)
    operation = ContextSetting(_tr.m[235, "Sum"])
    var_name = Setting("agg", schema_only=True)
    auto_apply = Setting(True)

    def __init__(self):
        super().__init__()
        self.data = None
        self.features = None

        self.selection_box = gui.vBox(self.controlArea, _tr.m[236, "Variable selection"])
        self.selection_group = QButtonGroup(self.selection_box)
        for i, label in enumerate((_tr.m[237, "All"],
                                   _tr.m[238, "All, including meta attributes"],
                                   _tr.m[239, "Features from separate input signal"],
                                   _tr.m[240, "Selected variables"])):
            button = QRadioButton(label)
            if i == self.selection_method:
                button.setChecked(True)
            self.selection_group.addButton(button, id=i)
            self.selection_box.layout().addWidget(button)
        self.selection_group.idClicked.connect(self._on_sel_method_changed)

        self.variable_model = DomainModel(
            order=(DomainModel.ATTRIBUTES, DomainModel.METAS),
            valid_types=ContinuousVariable)
        pixm: QStyle = self.style().pixelMetric
        ind_width = pixm(QStyle.PM_ExclusiveIndicatorWidth) + \
                    pixm(QStyle.PM_RadioButtonLabelSpacing)
        var_list = gui.listView(
            gui.indentedBox(self.selection_box, ind_width), self, "variables",
            model=self.variable_model,
            callback=self.commit.deferred
        )
        var_list.setSelectionMode(var_list.ExtendedSelection)

        box = gui.vBox(self.controlArea, box=_tr.m[241, "Operation"])
        combo = self.operation_combo = QComboBox()
        combo.addItems([op.name for op in self.Operations.values()])
        combo.textActivated[str].connect(self._on_operation_changed)
        combo.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        combo.setCurrentText(self.Operations[self.operation].name)
        box.layout().addWidget(combo)

        gui.lineEdit(
            box, self, "var_name",
            label=_tr.m[242, "Output variable name: "], orientation=Qt.Horizontal,
            callback=self.commit.deferred
        )

        gui.auto_apply(self.buttonsArea, self)

        self._update_selection_buttons()


    @Inputs.data
    def set_data(self, data: Table = None):
        self.closeContext()
        self.variables.clear()
        self.data = data
        if self.data:
            self.variable_model.set_domain(data.domain)
            self.openContext(data)
            self.operation_combo.setCurrentText(self.Operations[self.operation].name)
        else:
            self.variable_model.set_domain(None)

    @Inputs.features
    def set_features(self, features):
        if features is None:
            self.features = None
            missing = []
        else:
            self.features = [attr for attr in features if attr.is_continuous]
            missing = self._missing(features, self.features)
        self.Warning.discrete_features(missing, shown=bool(missing))

    def _update_selection_buttons(self):
        if self.features is not None:
            for i, button in enumerate(self.selection_group.buttons()):
                button.setChecked(i == self.InputFeatures)
                button.setEnabled(i == self.InputFeatures)
            self.controls.variables.setEnabled(False)
        else:
            for i, button in enumerate(self.selection_group.buttons()):
                button.setChecked(i == self.selection_method)
                button.setEnabled(i != self.InputFeatures)
            self.controls.variables.setEnabled(
                self.selection_method == self.SelectManually)

    def handleNewSignals(self):
        self._update_selection_buttons()
        self.commit.now()

    def _on_sel_method_changed(self, i):
        self.selection_method = i
        self._update_selection_buttons()
        self.commit.deferred()

    def _on_operation_changed(self, oper):
        self.operation = self.KeyFromDesc[oper]
        self.commit.deferred()

    @gui.deferred
    def commit(self):
        augmented = self._compute_data()
        self.Outputs.data.send(augmented)

    def _compute_data(self):
        self.Warning.missing_features.clear()
        if not self.data:
            return self.data

        variables = self._variables()
        if not self.data or not variables:
            return self.data

        new_col = self._compute_column(variables)
        new_var = self._new_var(variables)
        return self.data.add_column(new_var, new_col)

    def _variables(self):
        self.Warning.missing_features.clear()
        if self.features is not None:
            selected = [attr for attr in self.features
                        if attr in self.data.domain]
            missing = self._missing(self.features, selected)
            self.Warning.missing_features(missing, shown=bool(missing))
            return selected

        assert self.data

        domain = self.data.domain
        if self.selection_method == self.SelectAll:
            return [attr for attr in domain.attributes
                    if attr.is_continuous]
        if self.selection_method == self.SelectAllAndMeta:
            # skip separators
            return [attr for attr in chain(domain.attributes, domain.metas)
                    if attr.is_continuous]

        assert self.selection_method == self.SelectManually
        return self.variables

    def _compute_column(self, variables):
        arr = np.empty((len(self.data), len(variables)))
        for i, var in enumerate(variables):
            arr[:, i] = self.data.get_column(var)
        func = self.Operations[self.operation].func
        return func(arr, axis=1)

    def _new_var_name(self):
        return get_unique_names(self.data.domain, self.var_name)

    def _new_var(self, variables):
        name = self._new_var_name()
        if self.Operations[self.operation].time_preserving \
                and all(isinstance(var, TimeVariable) for var in variables):
            return TimeVariable(name)
        return ContinuousVariable(name)

    def send_report(self):
        if not self.data:
            return
        variables = self._variables()
        if not variables:
            return
        var_list = self._and_others(variables, 30)
        self.report_items((
            (_tr.m[243, "Output:"],
             _tr.e(_tr.c(244, f"'{self._new_var_name()}' as {self.operation.lower()} of {var_list}"))
            ),
        ))

    @staticmethod
    def _and_others(variables, limit):
        if len(variables) == 1:
            return f"'{variables[0].name}'"
        var_list = ", ".join(f"'{var.name}'"
                             for var in variables[:limit + 1][:-1])
        if len(variables) > limit:
            var_list += _tr.e(_tr.c(245, f" and {len(variables) - limit} more"))
        else:
            var_list += _tr.e(_tr.c(246, f" and '{variables[-1].name}'"))
        return var_list

    @classmethod
    def _missing(cls, given, used):
        if len(given) == len(used):
            return ""
        used = set(used)
        # Don't use set difference because it loses order
        missing = [attr for attr in given if attr not in used]
        return cls._and_others(missing, 5)


if __name__ == "__main__":  # pragma: no cover
    brown = Table("brown-selected")
    WidgetPreview(OWAggregateColumns).run(set_data=brown)
