from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from functools import partial
from types import SimpleNamespace
from typing import NamedTuple, Dict, List

import numpy as np
import scipy.sparse as sp

from AnyQt.QtCore import Qt, QSize, QAbstractListModel, QObject, \
    QItemSelectionModel
from AnyQt.QtGui import QColor
from AnyQt.QtWidgets import QButtonGroup, QRadioButton, QListView

from orangewidget.utils import listview
from orangewidget.utils.itemmodels import SeparatedListDelegate, \
    LabelledSeparator

from Orange.data import DiscreteVariable, ContinuousVariable, Domain, Table
from Orange.preprocess import Continuize as Continuizer
from Orange.preprocess.transformation import Identity, Indicator, Normalizer
from Orange.widgets import gui, widget
from Orange.widgets.settings import Setting
from Orange.widgets.utils.itemmodels import DomainModel
from Orange.widgets.utils.sql import check_sql_input
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import Input, Output


class MethodDesc(NamedTuple):
    id_: int
    label: str  # Label used for radio button
    short_desc: str  # Short description for list views
    tooltip: str  # Tooltip for radio button
    supports_sparse: bool = True


DefaultKey = ""
DefaultId = 99
BackCompatClass = object()

Continuize = SimpleNamespace(
    Default=DefaultId,
    **{v.name: v.value for v in Continuizer.MultinomialTreatment})

DiscreteOptions: Dict[int, MethodDesc] = {
    method.id_: method
    for method in (
        MethodDesc(
            Continuize.Default, _tr.m[317, "Use preset"], _tr.m[318, "preset"],
            _tr.m[319, "Treat the variable as defined in preset"]),
        MethodDesc(
            Continuize.Leave, _tr.m[320, "Keep categorical"], _tr.m[321, "keep as is"],
            _tr.m[322, "Keep the variable discrete"]),
        MethodDesc(
            Continuize.FirstAsBase, _tr.m[323, "First value as base"], _tr.m[324, "first as base"],
            _tr.m[325, "One indicator variable for each value except the first"]),
        MethodDesc(
            Continuize.FrequentAsBase, _tr.m[326, "Most frequent as base"], _tr.m[327, "frequent as base"],
            _tr.m[328, "One indicator variable for each value except the most frequent"],
            False),
        MethodDesc(
            Continuize.Indicators, _tr.m[329, "One-hot encoding"], _tr.m[330, "one-hot"],
            _tr.m[331, "One indicator variable for each value"],
            False),
        MethodDesc(
            Continuize.RemoveMultinomial, _tr.m[332, "Remove if more than 2 values"], _tr.m[333, "remove if >2"],
            _tr.m[334, "Remove variables with more than two values; indicator otherwise"]),
        MethodDesc(
            Continuize.Remove, _tr.m[335, "Remove"], _tr.m[336, "remove"],
            _tr.m[337, "Remove variable"]),
        MethodDesc(
            Continuize.AsOrdinal, _tr.m[338, "Treat as ordinal"], _tr.m[339, "as ordinal"],
            _tr.m[340, "Each value gets a consecutive number from 0 to number of values - 1"]),
        MethodDesc(
            Continuize.AsNormalizedOrdinal, _tr.m[341, "Treat as normalized ordinal"], _tr.m[342, "as norm. ordinal"],
            _tr.m[343, "Same as above, but scaled to [0, 1]"])
    )}

ContinuizationDefault = Continuize.FirstAsBase


Normalize = SimpleNamespace(Default=DefaultId,
                            Leave=0, Standardize=1, Center=2, Scale=3,
                            Normalize11=4, Normalize01=5)

ContinuousOptions: Dict[int, MethodDesc] = {
    method.id_: method
    for method in (
        MethodDesc(
            Normalize.Default, _tr.m[344, "Use preset"], _tr.m[345, "preset"],
            _tr.m[346, "Treat the variable as defined in 'default setting'"]),
        MethodDesc(
            Normalize.Leave, _tr.m[347, "Keep as it is"], _tr.m[348, "no change"],
            _tr.m[349, "Keep the variable as it is"]),
        MethodDesc(
            Normalize.Standardize, _tr.m[350, "Standardize to μ=0, σ²=1"], _tr.m[351, "standardize"],
            _tr.m[352, "Subtract the mean and divide by standard deviation"],
            False),
        MethodDesc(
            Normalize.Center, _tr.m[353, "Center to μ=0"], _tr.m[354, "center"],
            _tr.m[355, "Subtract the mean"],
            False),
        MethodDesc(
            Normalize.Scale, _tr.m[356, "Scale to σ²=1"], _tr.m[357, "scale"],
            _tr.m[358, "Divide by standard deviation"]),
        MethodDesc(
            Normalize.Normalize11, _tr.m[359, "Normalize to interval [-1, 1]"], _tr.m[360, "to [-1, 1]"],
            _tr.m[361, "Linear transformation into interval [-1, 1]"],
            False),
        MethodDesc(
            Normalize.Normalize01, _tr.m[362, "Normalize to interval [0, 1]"], _tr.m[363, "to [0, 1]"],
            _tr.m[364, "Linear transformation into interval [0, 1]"],
            False),
    )}

NormalizationDefault = Normalize.Leave


class ContDomainModel(DomainModel):
    HintRole = next(gui.OrangeUserRole)
    FilterRole = next(gui.OrangeUserRole)
    """Domain model that adds description of chosen methods"""
    def __init__(self, valid_type):
        super().__init__(
            order=(DomainModel.ATTRIBUTES,
                   LabelledSeparator(_tr.m[365, "Meta attributes"]), DomainModel.METAS,
                   LabelledSeparator(_tr.m[366, "Targets"]), DomainModel.CLASSES),
            valid_types=(valid_type, ), strict_type=True)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.ToolTipRole:
            return None
        if role == self.FilterRole:
            name = super().data(index, Qt.DisplayRole)
            if not isinstance(name, str):
                return None
            hint = index.data(self.HintRole)
            if hint is None:
                return name
            return f"{name} {hint[0]}"
        value = super().data(index, role)
        if role == Qt.DisplayRole:
            if isinstance(value, LabelledSeparator):
                return None
            return value, *(index.data(self.HintRole) or ("", False))
        return value


class DefaultContModel(QAbstractListModel):
    """A model used for showing "Default settings" above the list view"""
    icon = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if DefaultContModel.icon is None:
            DefaultContModel.icon = gui.createAttributePixmap(
                "★", QColor(0, 0, 0, 0), Qt.black)
        self.method = ""

    @staticmethod
    def rowCount(parent):
        return 0 if parent.isValid() else 1

    @staticmethod
    def columnCount(parent):
        return 0 if parent.isValid() else 1

    def data(self, _, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return _tr.e(_tr.c(367, f"Preset: {self.method}"))
        elif role == Qt.DecorationRole:
            return self.icon
        elif role == Qt.ToolTipRole:
            return _tr.m[368, "Default for variables without specific settings"]
        return None

    def setMethod(self, method):
        self.method = method
        self.dataChanged.emit(self.index(0, 0), self.index(0, 0))


class ListViewSearch(listview.ListViewSearch):
    """
    A list view with two components shown above it:
    - a listview containing a single item representing default settings
    - a filter for search

    The class is based on listview.ListViewSearch and needs to have the same
    name in order to override its private method __layout.

    Inherited __init__ calls __layout, so `default_view` must be constructed
    there. Construction before calling super().__init__ doesn't work because
    PyQt does not allow it.
    """
    class Delegate(SeparatedListDelegate):
        """
        A delegate that shows items (variables) with specific settings in bold
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._default_hints = False

        def initStyleOption(self, option, index):
            super().initStyleOption(option, index)
            hint = index.data(ContDomainModel.HintRole)
            option.font.setBold(hint is not None and hint[1])

        def set_default_hints(self, show):
            self._default_hints = show

        def displayText(self, value, _):
            if value is None:
                return None
            name, hint, nondefault = value
            if self._default_hints or nondefault:
                name += f": {hint}"
            return name

    def __init__(self, *args, **kwargs):
        self.default_view = None
        super().__init__(preferred_size=QSize(350, -1), *args, **kwargs)
        self.setItemDelegate(self.Delegate(self))
        self.force_hints = False

    def select_default(self):
        """Select the item representing default settings"""
        self.default_view.selectionModel().select(
            self.default_view.model().index(0),
            QItemSelectionModel.Select)

    def set_default_method(self, method):
        self.default_view.model().setMethod(method)

    # pylint: disable=unused-private-member
    def __layout(self):
        if self.default_view is None:  # __layout was called from __init__
            view = self.default_view = QListView(self)
            view.setModel(DefaultContModel())
            self.filterProxyModel().setFilterRole(ContDomainModel.FilterRole)
            view.verticalScrollBar().setDisabled(True)
            view.horizontalScrollBar().setDisabled(True)
            view.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            view.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            font = view.font()
            font.setBold(True)
            view.setFont(font)
        else:
            view = self.default_view

        # Put the list view with default on top
        margins = self.viewportMargins()
        def_height = view.sizeHintForRow(0) + 2 * view.spacing() + 2
        view.setGeometry(0, 0, self.geometry().width(), def_height)
        view.setFixedHeight(def_height)

        # Then search
        search = self.__search
        src_height = search.sizeHint().height()
        size = self.size()
        search.setGeometry(0, def_height + 2, size.width(), src_height)

        # Then the real list view
        margins.setTop(def_height + 2 + src_height)
        self.setViewportMargins(margins)

    def event(self, ev):
        if ev.type() == ev.ToolTip:
            self.itemDelegate().set_default_hints(True)
            self.viewport().update()
            return True
        return super().event(ev)

    def leaveEvent(self, _):
        self.itemDelegate().set_default_hints(False)
        self.viewport().update()


class OWContinuize(widget.OWWidget):
    # Many false positives for `hints`; pylint ignores type annotations
    # pylint: disable=unsubscriptable-object,unsupported-assignment-operation
    # pylint: disable=unsupported-membership-test, unsupported-delete-operation
    name = _tr.m[369, "Continuize"]
    description = (_tr.m[370, "Transform categorical attributes into numeric and, "] +
                   _tr.m[371, "optionally, scale numeric values."])
    icon = "icons/Continuize.svg"
    category = _tr.m[372, "Transform"]
    keywords = _tr.m[373, "continuize, encode, dummy, numeric, one-hot, binary, treatment, contrast"]
    priority = 2120

    class Inputs:
        data = Input(_tr.m[374, "Data"], Table)

    class Outputs:
        data = Output(_tr.m[375, "Data"], Table)

    class Error(widget.OWWidget.Error):
        unsupported_sparse = \
            widget.Msg(_tr.m[376, "Some chosen methods do not support sparse data: {}"])

    want_control_area = False

    settings_version = 3
    disc_var_hints: Dict[str, int] = Setting(
        {DefaultKey: ContinuizationDefault}, schema_only=True)
    cont_var_hints: Dict[str, int] = Setting(
        {DefaultKey: NormalizationDefault}, schema_only=True)
    autosend = Setting(True)

    def __init__(self):
        super().__init__()
        self.data = None
        self._var_cache = {}

        def create(title, vartype, methods):
            hbox = gui.hBox(box, title)
            view = ListViewSearch(
                selectionMode=ListViewSearch.ExtendedSelection,
                uniformItemSizes=True)
            view.setModel(ContDomainModel(vartype))
            view.selectionModel().selectionChanged.connect(
                lambda: self._on_var_selection_changed(view))
            view.default_view.selectionModel().selectionChanged.connect(
                lambda selected: self._on_default_selected(view, selected))
            hbox.layout().addWidget(view)

            bbox = gui.vBox(hbox)
            bgroup = QButtonGroup(self)
            bgroup.idClicked.connect(self._on_radio_clicked)
            for desc in methods.values():
                button = QRadioButton(desc.label)
                button.setToolTip(desc.tooltip)
                bgroup.addButton(button, desc.id_)
                bbox.layout().addWidget(button)
            bbox.layout().addStretch(1)
            return hbox, view, bbox, bgroup

        box = gui.vBox(self.mainArea, True, spacing=8)
        self.disc_box, self.disc_view, self.disc_radios, self.disc_group = \
            create(_tr.m[377, "Categorical Variables"], DiscreteVariable, DiscreteOptions)
        self.disc_view.set_default_method(
            DiscreteOptions[self.disc_var_hints[DefaultKey]].short_desc)
        self.disc_view.select_default()

        self.cont_box, self.cont_view, self.cont_radios, self.cont_group = \
            create(_tr.m[378, "Numeric Variables"], ContinuousVariable, ContinuousOptions)
        self.cont_view.set_default_method(
            ContinuousOptions[self.cont_var_hints[DefaultKey]].short_desc)
        self.cont_view.select_default()

        boxes = (self.disc_radios, self.cont_radios)
        width = max(box.sizeHint().width() for box in boxes)
        for box in boxes:
            box.setFixedWidth(width)

        box = gui.hBox(self.mainArea)
        gui.button(
            box, self, _tr.m[379, "Reset All"], callback=self._on_reset_hints,
            autoDefault=False)
        gui.rubber(box)
        gui.auto_apply(box, self, "autosend")

    def _on_var_selection_changed(self, view):
        if not view.selectionModel().selectedIndexes():
            # Prevent infinite recursion (with _on_default_selected)
            return
        view.default_view.selectionModel().clearSelection()
        self._update_radios(view)

    def _on_default_selected(self, view, selected):
        if not selected:
            # Prevent infinite recursion (with _var_selection_selected)
            return
        view.selectionModel().clearSelection()
        self._update_radios(view)

    def selected_vars(self, view) -> List[str]:
        """
        Return selected variables

        If 'Default settings' are selected, this returns DefaultKey
        """
        model = view.model()
        return [model[index.row()]
                for index in view.selectionModel().selectedRows()]

    def _update_radios(self, view):
        if view is self.disc_view:
            group, hints = self.disc_group, self.disc_var_hints
        else:
            group, hints = self.cont_group, self.cont_var_hints

        selvars = self.selected_vars(view)
        if not selvars:
            self._check_button(group, hints[DefaultKey], True)
            self._set_radio_enabled(group, DefaultId, False)
            return

        self._set_radio_enabled(group, DefaultId, True)
        options = {hints.get(var.name, self.default_for_var(var))
                   for var in selvars}
        if len(options) == 1:
            self._check_button(group, options.pop(), True)
        else:
            self._uncheck_all_buttons(group)

    @staticmethod
    def _uncheck_all_buttons(group: QButtonGroup):
        button = group.checkedButton()
        if button is not None:
            group.setExclusive(False)
            button.setChecked(False)
            group.setExclusive(True)

    def _set_radio_enabled(
            self, group: QButtonGroup, method_id: int, value: bool):
        if group.button(method_id).isChecked() and not value:
            self._uncheck_all_buttons(group)
        group.button(method_id).setEnabled(value)

    @staticmethod
    def _check_button(group: QButtonGroup, method_id: int, checked: bool):
        group.button(method_id).setChecked(checked)

    def _on_radio_clicked(self, method_id: int):
        if QObject().sender() is self.disc_group:
            view, hints, methods = \
                self.disc_view, self.disc_var_hints, DiscreteOptions
            leave_id = Continuize.Leave
        else:
            view, hints, methods = \
                self.cont_view, self.cont_var_hints, ContinuousOptions
            leave_id = Normalize.Leave
        selvars = self.selected_vars(view)
        if not selvars:
            hints[DefaultKey] = method_id
            view.set_default_method(methods[method_id].short_desc)
        else:
            keys = [var.name for var in selvars]
            indexes = view.selectionModel().selectedIndexes()
            model = view.model()
            # These two keys may delete values from dict, hence we must loop
            if method_id in (DefaultId, leave_id):
                for key in keys:
                    # Attributes do not store the hint if it equals Default;
                    # metas and targets do not store it if it is Leave
                    if method_id == (DefaultId if self.is_attr(key) else leave_id):
                        if key in hints:
                            del hints[key]
                    else:
                        hints[key] = method_id
            else:
                hints.update(dict.fromkeys(keys, method_id))
            desc = methods[method_id].short_desc
            for index, var in zip(indexes, selvars):
                show = method_id != self.default_for_var(var)
                model.setData(index, (desc, show), model.HintRole)
        self.commit.deferred()

    @Inputs.data
    @check_sql_input
    def set_data(self, data):
        self.data = data
        self._var_cache.clear()
        domain = data.domain if data else None
        self.disc_view.model().set_domain(domain)
        self.cont_view.model().set_domain(domain)
        if data:
            # Clean up hints only when receiving new data, not on disconnection
            self._set_hints()
        self.commit.now()

    def _set_hints(self):
        assert self.data

        # Backward compatibility for settings < 3
        class_treatment = self.disc_var_hints.get(BackCompatClass, None)
        if class_treatment is not None \
                and self.data.domain.class_var is not None:
            self.disc_var_hints[self.data.domain.class_var.name] \
                = class_treatment

        for hints, model, options in (
                (self.cont_var_hints, self.cont_view.model(), ContinuousOptions),
                (self.disc_var_hints, self.disc_view.model(), DiscreteOptions)):
            filtered = {DefaultKey: hints[DefaultKey]}
            for i, var in enumerate(model):
                if isinstance(var, LabelledSeparator):
                    continue
                default = self.default_for_var(var)
                method_id = hints.get(var.name, default)
                nondefault = method_id != default
                if nondefault:
                    filtered[var.name] = method_id
                model.setData(
                    model.index(i, 0),
                    (options[method_id].short_desc, nondefault),
                    model.HintRole)
            hints.clear()
            hints.update(filtered)

    def _on_reset_hints(self):
        if not self.data:
            return
        self.cont_var_hints.clear()
        self.disc_var_hints.clear()
        self.disc_var_hints[DefaultKey] = ContinuizationDefault
        self.cont_var_hints[DefaultKey] = NormalizationDefault
        self._set_hints()
        self.cont_view.set_default_method(
            ContinuousOptions[ContinuizationDefault].short_desc)
        self.disc_view.set_default_method(
            ContinuousOptions[NormalizationDefault].short_desc)

    @gui.deferred
    def commit(self):
        self.Outputs.data.send(self._prepare_output())

    def _prepare_output(self):
        self.Error.unsupported_sparse.clear()
        if not self.data:
            return None
        if unsupp_sparse := self._unsupported_sparse():
            if len(unsupp_sparse) == 1:
                self.Error.unsupported_sparse(unsupp_sparse[0])
            else:
                self.Error.unsupported_sparse("\n" + ", ".join(unsupp_sparse))
            return None

        domain = self.data.domain
        attrs = self._create_vars(domain.attributes)
        class_vars = self._create_vars(domain.class_vars)
        metas = self._create_vars(domain.metas)
        return self.data.transform(Domain(attrs, class_vars, metas))

    def _unsupported_sparse(self):
        # time is not continuous, pylint: disable=unidiomatic-typecheck
        domain = self.data.domain
        disc = set()
        cont = set()
        # At the time of writing, self.data.Y cannot be sparse (setter for
        # `Y` converts it to dense, as done in
        # https://github.com/biolab/orange3/commit/a18f38059caf37f3b329d6ad688189561959bb24)
        # Including it here doesn't hurt, though.
        for part, attrs in ((self.data.X, domain.attributes),
                            (self.data.Y, domain.class_vars),
                            (self.data.metas, domain.metas)):
            if sp.issparse(part):
                disc |= {self._hint_for_var(var)
                         for var in attrs
                         if var.is_discrete}
                cont |= {self._hint_for_var(var)
                         for var in attrs
                         if type(var) is ContinuousVariable}
        disc &= {method.id_
                 for method in DiscreteOptions.values()
                 if not method.supports_sparse}
        cont &= {method.id_
                 for method in ContinuousOptions.values()
                 if not method.supports_sparse}

        # Retrieve them from DiscreteOptions/ContinuousOptions to keep the order
        return [method.label
                for methods, problems in ((DiscreteOptions, disc),
                                          (ContinuousOptions, cont))
                for method in methods.values() if method.id_ in problems]

    def _create_vars(self, part):
        # time is not continuous, pylint: disable=unidiomatic-typecheck
        return sum(
            (self._continuized_vars(var) if var.is_discrete
             else self._scaled_vars(var) if type(var) is ContinuousVariable
             else [var]
             for var in part),
            start=[])

    def _get(self, var, stat):
        def most_frequent(col):
            col = col[np.isfinite(col)].astype(int)
            counts = np.bincount(col, minlength=len(var.values))
            return np.argmax(counts)

        funcs = {"min": np.nanmin, "max": np.nanmax,
                 "mean": np.nanmean, "std": np.nanstd,
                 "major": most_frequent}
        name = var.name
        cache = self._var_cache.setdefault(name, {})
        if stat not in cache:
            cache[stat] = funcs[stat](self.data.get_column(var))
        return cache[stat]

    def is_attr(self, var):
        domain = self.data.domain
        return 0 <= domain.index(var) < len(domain.attributes)

    def default_for_var(self, var):
        if self.is_attr(var):
            return DefaultId
        return Continuize.Leave if var.is_discrete else Normalize.Leave

    def _hint_for_var(self, var):
        if var.is_discrete:
            hints, leave_id = self.disc_var_hints, Continuize.Leave
        else:
            hints, leave_id = self.cont_var_hints, Normalize.Leave

        # Default for attributes is given by "default"
        if self.is_attr(var):
            return hints.get(var.name, hints[DefaultKey])

        # For metas and targets, default is Leave
        # If user changes it to "Default", default is used
        hint = hints.get(var.name, leave_id)
        if hint == DefaultId:
            hint = hints[DefaultKey]
        return hint

    def _scaled_vars(self, var):
        hint = self._hint_for_var(var)
        if hint == Normalize.Leave:
            return [var]

        get = partial(self._get, var)
        if hint == Normalize.Standardize:
            off, scale = get("mean"), 1 / (get("std") or 1)
        elif hint == Normalize.Center:
            off, scale = get("mean"), 1
        elif hint == Normalize.Scale:
            off, scale = 0, 1 / (get("std") or 1)
        else:
            assert hint in (Normalize.Normalize11, Normalize.Normalize01), f"hint={hint}?!"
            min_, max_ = get("min"), get("max")
            span = (max_ - min_) or 1
            if hint == Normalize.Normalize11:
                off, scale = (min_ + max_) / 2, 2 / span
            else:
                off, scale = min_, 1 / span

        return [ContinuousVariable(
            var.name,
            compute_value=Normalizer(var, off, scale))]

    def _continuized_vars(self, var, hint=None):
        if hint is None:
            hint = self._hint_for_var(var)

        # Single variable
        if hint == Continuize.Leave:
            return [var]
        if hint == Continuize.Remove:
            return []
        if hint == Continuize.RemoveMultinomial and len(var.values) <= 2 or \
                hint == Continuize.AsOrdinal:
            return [ContinuousVariable(var.name,
                                       compute_value=Identity(var))]
        if hint == Continuize.RemoveMultinomial:
            assert len(var.values) > 2
            return []
        if hint == Continuize.AsOrdinal:
            return [ContinuousVariable(var.name,
                                       compute_value=Identity(var))]
        if hint == Continuize.AsNormalizedOrdinal:
            scale = 1 / (len(var.values) - 1 or 1)
            return [ContinuousVariable(var.name,
                                       compute_value=Normalizer(var, 0, scale))]

        # Multiple dummy variables
        if hint == Continuize.FirstAsBase:
            base = 0
        elif hint == Continuize.FrequentAsBase:
            base = self._get(var, "major")
        elif hint == Continuize.Indicators:
            base = None
        else:
            assert False, f"hint={hint}?!"
        return [
            ContinuousVariable(f"{var.name}={value}",
                               compute_value=Indicator(var, value=i))
            for i, value in enumerate(var.values)
            if i != base
        ]

    def send_report(self):
        if not self.data:
            return
        single_disc = len(self.disc_view.model()) > 0 \
                      and len(self.disc_var_hints) == 1 \
                      and DiscreteOptions[self.disc_var_hints[DefaultKey]].label.lower()
        single_cont = len(self.cont_view.model()) > 0 \
                      and len(self.cont_var_hints) == 1 \
                      and ContinuousOptions[self.cont_var_hints[DefaultKey]].label.lower()
        if single_disc and single_cont:
            self.report_items(
                ((_tr.m[380, "Categorical variables"], single_disc),
                 (_tr.m[381, "Numeric variables"], single_cont))
            )
        else:
            if single_disc:
                self.report_paragraph(_tr.m[382, "Categorical variables"], single_disc)
            elif len(self.disc_view.model()) > 0:
                self.report_items(
                    _tr.m[383, "Categorical variables"],
                    [(_tr.m[384, "Preset"] if name == DefaultKey else name,
                      DiscreteOptions[id_].label.lower())
                     for name, id_ in self.disc_var_hints.items()])
            if single_cont:
                self.report_paragraph(_tr.m[385, "Numeric variables"], single_cont)
            elif len(self.cont_view.model()) > 0:
                self.report_items(
                    _tr.m[386, "Numeric variables"],
                    [(_tr.m[387, "Preset"] if name == DefaultKey else name,
                      ContinuousOptions[id_].label.lower())
                     for name, id_ in self.cont_var_hints.items()])
            self.report_paragraph(_tr.m[388, "Unlisted"],
                (_tr.m[389, "Any unlisted attributes default to preset option, and "] + (_tr.m[390, "unlisted meta attributes and target variables are kept "] + _tr.m[391, "as they are"])))

    @classmethod
    def migrate_settings(cls, settings, version):
        if version < 2:
            cont_treat = settings.pop("continuous_treatment", 0)
            zero_based = settings.pop("zero_based", True)
            if cont_treat == 1:
                if zero_based:
                    settings["continuous_treatment"] = Normalize.Normalize01
                else:
                    settings["continuous_treatment"] = Normalize.Normalize11
            elif cont_treat == 2:
                settings["continuous_treatment"] = Normalize.Standardize
        if version < 3:
            settings["cont_var_hints"] = \
                {DefaultKey:
                 settings.pop("continuous_treatment", Normalize.Leave)}

            # DISC OPS: Default=99, Indicators=1, FirstAsBase=2, FrequentAsBase=3, Remove=4,
            # RemoveMultinomial=5, ReportError=6, AsOrdinal=7, AsNormalizedOrdinal=8, Leave=9

            # OLD ORDER: [FirstAsBase, FrequentAsBase, Indicators, RemoveMultinomial, Remove,
            # AsOrdinal, AsNormalizedOrdinal]
            old_to_new = [2, 3, 1, 5, 4, 7, 8]

            settings["disc_var_hints"] = \
                {DefaultKey:
                 old_to_new[settings.pop("multinomial_treatment", 0)]}

            # OLD ORDER: [Leave, AsOrdinal, AsNormalizedOrdinal, Indicators]
            old_to_new = [9, 7, 8, 1]

            class_treatment = old_to_new[settings.pop("class_treatment", 0)]
            if class_treatment != Continuize.Leave:
                settings["disc_var_hints"][BackCompatClass] = class_treatment


# Backward compatibility for unpickling settings
OWContinuize.Normalize = Normalize


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWContinuize).run(Table("heart_disease"))
