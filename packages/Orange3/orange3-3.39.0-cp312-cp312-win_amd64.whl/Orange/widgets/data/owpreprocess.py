from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from collections import OrderedDict
import importlib.resources

import numpy

from AnyQt.QtWidgets import (
    QWidget, QButtonGroup, QGroupBox, QRadioButton, QSlider,
    QDoubleSpinBox, QComboBox, QSpinBox, QListView, QLabel,
    QScrollArea, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSizePolicy, QApplication, QCheckBox
)

from AnyQt.QtGui import (
    QIcon, QStandardItemModel, QStandardItem
)

from AnyQt.QtCore import (
    Qt, QEvent, QSize, QMimeData, QTimer
)

from AnyQt.QtCore import pyqtSignal as Signal, pyqtSlot as Slot

from orangewidget.gui import Slider

import Orange.data
from Orange import preprocess
from Orange.preprocess import Continuize, ProjectPCA, RemoveNaNRows, \
    ProjectCUR, Scale as _Scale, Randomize as _Randomize, RemoveSparse
from Orange.widgets import widget, gui
from Orange.widgets.utils.localization import pl
from Orange.widgets.settings import Setting
from Orange.widgets.utils.overlay import OverlayWidget
from Orange.widgets.utils.sql import check_sql_input
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import Input, Output
from Orange.preprocess import Normalize
from Orange.widgets.data.utils.preprocess import (
    BaseEditor, blocked, StandardItemModel, DescriptionRole,
    ParametersRole, Controller, SequenceFlow
)


class _NoneDisc(preprocess.discretize.Discretization):
    """Discretize all variables into None.

    Used in combination with preprocess.Discretize to remove
    all discrete features from the domain.

    """
    _reprable_module = True

    def __call__(self, data, variable):
        return None


class DiscretizeEditor(BaseEditor):
    """
    Editor for preprocess.Discretize.
    """
    #: Discretize methods
    NoDisc, EqualWidth, EqualFreq, Drop, EntropyMDL = 0, 1, 2, 3, 4
    Discretizers = {
        NoDisc: (None, {}),
        EqualWidth: (preprocess.discretize.EqualWidth, {"n": 4}),
        EqualFreq:  (preprocess.discretize.EqualFreq, {"n": 4}),
        Drop: (_NoneDisc, {}),
        EntropyMDL: (preprocess.discretize.EntropyMDL, {"force": False})
    }
    Names = {
        NoDisc: _tr.m[1219, "None"],
        EqualWidth: _tr.m[1220, "Equal width discretization"],
        EqualFreq: _tr.m[1221, "Equal frequency discretization"],
        Drop: _tr.m[1222, "Remove numeric features"],
        EntropyMDL: _tr.m[1223, "Entropy-MDL discretization"]
    }

    def __init__(self, parent=None, **kwargs):
        BaseEditor.__init__(self, parent, **kwargs)
        self.__method = DiscretizeEditor.EqualFreq
        self.__nintervals = 4

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.__group = group = QButtonGroup(self, exclusive=True)

        for method in [self.EntropyMDL, self.EqualFreq, self.EqualWidth,
                       self.Drop]:
            rb = QRadioButton(
                self, text=self.Names[method],
                checked=self.__method == method
            )
            layout.addWidget(rb)
            group.addButton(rb, method)

        group.buttonClicked.connect(self.__on_buttonClicked)

        self.__slbox = slbox = QGroupBox(
            title=_tr.m[1224, "Number of intervals (for equal width/frequency)"],
            flat=True
        )
        slbox.setLayout(QHBoxLayout())
        self.__slider = slider = Slider(
            orientation=Qt.Horizontal,
            minimum=2, maximum=10, value=self.__nintervals,
            enabled=self.__method in [self.EqualFreq, self.EqualWidth],
            pageStep=1, tickPosition=QSlider.TicksBelow
        )
        slider.valueChanged.connect(self.__on_valueChanged)
        slbox.layout().addWidget(slider)
        self.__slabel = slabel = QLabel()
        slbox.layout().addWidget(slabel)

        container = QHBoxLayout()
        container.setContentsMargins(13, 0, 0, 0)
        container.addWidget(slbox)
        self.layout().insertLayout(3, container)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

    def setMethod(self, method):
        if self.__method != method:
            self.__method = method
            b = self.__group.button(method)
            b.setChecked(True)
            self.__slider.setEnabled(
                method in [self.EqualFreq, self.EqualWidth]
            )
            self.changed.emit()

    def method(self):
        return self.__method

    def intervals(self):
        return self.__nintervals

    def setIntervals(self, n):
        n = numpy.clip(n, self.__slider.minimum(), self.__slider.maximum())
        n = int(n)
        if self.__nintervals != n:
            self.__nintervals = n
            # blocking signals in order to differentiate between
            # changed by user (notified through __on_valueChanged) or
            # changed programmatically (this)
            with blocked(self.__slider):
                self.__slider.setValue(n)
                self.__slabel.setText(str(self.__slider.value()))
            self.changed.emit()

    def setParameters(self, params):
        method = params.get("method", self.EqualFreq)
        nintervals = params.get("n", 5)
        self.setMethod(method)
        if method in [self.EqualFreq, self.EqualWidth]:
            self.setIntervals(nintervals)

    def parameters(self):
        if self.__method in [self.EqualFreq, self.EqualWidth]:
            return {"method": self.__method, "n": self.__nintervals}
        else:
            return {"method": self.__method}

    def __on_buttonClicked(self):
        # on user 'method' button click
        method = self.__group.checkedId()
        if method != self.__method:
            self.setMethod(self.__group.checkedId())
            self.edited.emit()

    def __on_valueChanged(self):
        # on user n intervals slider change.
        self.__nintervals = self.__slider.value()
        self.changed.emit()
        self.edited.emit()
        self.__slabel.setText(str(self.__slider.value()))

    @staticmethod
    def createinstance(params):
        params = dict(params)
        method = params.pop("method", DiscretizeEditor.EqualFreq)
        method, defaults = DiscretizeEditor.Discretizers[method]

        if method is None:
            return None

        resolved = dict(defaults)
        # update only keys in defaults?
        resolved.update(params)
        return preprocess.Discretize(method(**params), remove_const=False)

    def __repr__(self):
        n_int = _tr.m[1225, ", Number of intervals: {}"].format(self.__nintervals) \
            if self.__method in [self.EqualFreq, self.EqualWidth] else ""
        return "{}{}".format(self.Names[self.__method], n_int)


class ContinuizeEditor(BaseEditor):
    _Type = type(Continuize.FirstAsBase)

    Continuizers = OrderedDict([
        (Continuize.FrequentAsBase, _tr.m[1226, "Most frequent is base"]),
        (Continuize.Indicators, _tr.m[1227, "One feature per value"]),
        (Continuize.RemoveMultinomial, _tr.m[1228, "Remove non-binary features"]),
        (Continuize.Remove, _tr.m[1229, "Remove categorical features"]),
        (Continuize.AsOrdinal, _tr.m[1230, "Treat as ordinal"]),
        (Continuize.AsNormalizedOrdinal, _tr.m[1231, "Divide by number of values"])
    ])

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())
        self.__treatment = Continuize.Indicators
        self.__group = group = QButtonGroup(exclusive=True)
        group.buttonClicked.connect(self.__on_buttonClicked)

        for treatment, text in ContinuizeEditor.Continuizers.items():
            rb = QRadioButton(
                text=text,
                checked=self.__treatment == treatment)
            group.addButton(rb, enum_to_index(ContinuizeEditor._Type,
                                              treatment))
            self.layout().addWidget(rb)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def setTreatment(self, treatment):
        buttonid = enum_to_index(ContinuizeEditor._Type, treatment)
        b = self.__group.button(buttonid)
        if b is not None:
            b.setChecked(True)
            self.__treatment = treatment
            self.changed.emit()

    def treatment(self):
        return self.__treatment

    def setParameters(self, params):
        treatment = params.get("multinomial_treatment", Continuize.Indicators)
        self.setTreatment(treatment)

    def parameters(self):
        return {"multinomial_treatment": self.__treatment}

    def __on_buttonClicked(self):
        self.__treatment = index_to_enum(
            ContinuizeEditor._Type, self.__group.checkedId())
        self.changed.emit()
        self.edited.emit()

    @staticmethod
    def createinstance(params):
        params = dict(params)
        treatment = params.pop("multinomial_treatment", Continuize.Indicators)
        return Continuize(multinomial_treatment=treatment)

    def __repr__(self):
        return self.Continuizers[self.__treatment]


class RemoveSparseEditor(BaseEditor):
    options = [_tr.m[1232, "missing values"], _tr.m[1233, "zeros"]]

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.fixedThresh = 50
        self.percThresh = 5
        self.useFixedThreshold = False
        self.filter0 = True
        self.setLayout(QVBoxLayout())

        self.layout().addWidget(QLabel(_tr.m[1234, "Remove features with too many"]))
        self.filter_buttons = QButtonGroup(exclusive=True)
        self.filter_buttons.buttonClicked.connect(self.filterByClicked)
        for idx, option, in enumerate(self.options):
            btn = QRadioButton(self, text=option, checked=idx == 1)
            self.filter_buttons.addButton(btn, id=idx)
            self.layout().addWidget(btn)

        self.layout().addSpacing(20)

        filter_settings = QGroupBox(title=_tr.m[1235, 'Threshold:'], flat=True)
        filter_settings.setLayout(QFormLayout())
        self.settings_buttons = QButtonGroup(exclusive=True)
        self.settings_buttons.buttonClicked.connect(self.filterSettingsClicked)

        btn_perc = QRadioButton(self, text=_tr.m[1236, 'Percentage'], checked=not self.useFixedThreshold)
        self.settings_buttons.addButton(btn_perc, id=0)
        self.percSpin = QSpinBox(minimum=0, maximum=100, value=self.percThresh,
                                 enabled=not self.useFixedThreshold)
        self.percSpin.valueChanged[int].connect(self.setPercThresh)
        self.percSpin.editingFinished.connect(self.edited)

        btn_fix = QRadioButton(self, text=_tr.m[1237, 'Fixed'], checked=self.useFixedThreshold)
        self.settings_buttons.addButton(btn_fix, id=1)
        self.fixedSpin = QSpinBox(minimum=0, maximum=1000000, value=self.fixedThresh,
                                  enabled=self.useFixedThreshold)
        self.fixedSpin.valueChanged[int].connect(self.setFixedThresh)
        self.fixedSpin.editingFinished.connect(self.edited)
        filter_settings.layout().addRow(btn_fix, self.fixedSpin)
        filter_settings.layout().addRow(btn_perc, self.percSpin)

        self.layout().addWidget(filter_settings)

    def filterSettingsClicked(self):
        self.setUseFixedThreshold(self.settings_buttons.checkedId())
        self.percSpin.setEnabled(not self.useFixedThreshold)
        self.fixedSpin.setEnabled(self.useFixedThreshold)
        self.edited.emit()

    def filterByClicked(self):
        self.setFilter0(self.filter_buttons.checkedId())

    def setFilter0(self, id_):
        if self.filter0 != id_:
            self.filter0 = id_
            self.filter_buttons.button(id_).setChecked(True)
            self.edited.emit()

    def setFixedThresh(self, thresh):
        if self.fixedThresh != thresh:
            self.fixedThresh = thresh
            self.fixedSpin.setValue(thresh)
            self.edited.emit()

    def setPercThresh(self, thresh):
        if self.percThresh != thresh:
            self.percThresh = thresh
            self.percSpin.setValue(thresh)
            self.edited.emit()

    def setUseFixedThreshold(self, val):
        if self.useFixedThreshold != val:
            self.useFixedThreshold = val
            self.edited.emit()

    def parameters(self):
        return {'fixedThresh': self.fixedThresh,
                'percThresh' : self.percThresh,
                'useFixedThreshold' : self.useFixedThreshold,
                'filter0' : self.filter0}

    def setParameters(self, params):
        self.setPercThresh(params.get('percThresh', 5))
        self.setFixedThresh(params.get('fixedThresh', 50))
        self.setUseFixedThreshold(params.get('useFixedThreshold', False))
        self.setFilter0(params.get('filter0', True))

    @staticmethod
    def createinstance(params):
        params = dict(params)
        filter0 = params.pop('filter0', True)
        useFixedThreshold = params.pop('useFixedThreshold', False)
        if useFixedThreshold:
            threshold = params.pop('fixedThresh', 50)
        else:
            threshold = params.pop('percThresh', 5) / 100
        return RemoveSparse(threshold, filter0)

    def __repr__(self):
        desc = _tr.e(_tr.c(1238, f"remove features with too many {self.options[self.filter0]}, threshold: "))
        if self.useFixedThreshold:
            desc += _tr.e(_tr.c(1239, f"{self.fixedThresh} {pl(self.fixedThresh, 'instance')}"))
        else:
            desc += f"{self.percThresh} %"
        return desc


class ImputeEditor(BaseEditor):
    (NoImputation, Constant, Average,
     Model, Random, DropRows, DropColumns) = 0, 1, 2, 3, 4, 5, 6

    Imputers = {
        NoImputation: (None, {}),
        #         Constant: (None, {"value": 0})
        Average: (preprocess.impute.Average(), {}),
        #         Model: (preprocess.impute.Model, {}),
        Random: (preprocess.impute.Random(), {}),
        DropRows: (None, {})
    }
    Names = {
        NoImputation: _tr.m[1240, "Don't impute."],
        Constant: _tr.m[1241, "Replace with constant"],
        Average: _tr.m[1242, "Average/Most frequent"],
        Model: _tr.m[1243, "Model based imputer"],
        Random: _tr.m[1244, "Replace with random value"],
        DropRows: _tr.m[1245, "Remove rows with missing values."],
    }

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())

        self.__method = ImputeEditor.Average
        self.__group = group = QButtonGroup(self, exclusive=True)
        group.buttonClicked.connect(self.__on_buttonClicked)

        for methodid in [self.Average, self.Random, self.DropRows]:
            text = self.Names[methodid]
            rb = QRadioButton(text=text, checked=self.__method == methodid)
            group.addButton(rb, methodid)
            self.layout().addWidget(rb)

    def setMethod(self, method):
        b = self.__group.button(method)
        if b is not None:
            b.setChecked(True)
            self.__method = method
            self.changed.emit()

    def setParameters(self, params):
        method = params.get("method", ImputeEditor.Average)
        self.setMethod(method)

    def parameters(self):
        return {"method": self.__method}

    def __on_buttonClicked(self):
        self.__method = self.__group.checkedId()
        self.changed.emit()
        self.edited.emit()

    @staticmethod
    def createinstance(params):
        params = dict(params)
        method = params.pop("method", ImputeEditor.Average)
        if method == ImputeEditor.NoImputation:
            return None
        elif method == ImputeEditor.Average:
            return preprocess.Impute()
        elif method == ImputeEditor.Model:
            return preprocess.Impute(method=preprocess.impute.Model())
        elif method == ImputeEditor.DropRows:
            return RemoveNaNRows()
        elif method == ImputeEditor.DropColumns:
            return preprocess.RemoveNaNColumns()
        else:
            method, defaults = ImputeEditor.Imputers[method]
            defaults = dict(defaults)
            defaults.update(params)
            return preprocess.Impute(method=method)

    def __repr__(self):
        return self.Names[self.__method]


class UnivariateFeatureSelect(QWidget):
    changed = Signal()
    edited = Signal()

    #: Strategy
    Fixed, Proportion, FDR, FPR, FWE = 1, 2, 3, 4, 5

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())

        self.__scoreidx = 0
        self.__strategy = UnivariateFeatureSelect.Fixed
        self.__k = 10
        self.__p = 75.0

        box = QGroupBox(title=_tr.m[1246, "Score"], flat=True)
        box.setLayout(QVBoxLayout())
        self.__cb = cb = QComboBox(self, )
        self.__cb.currentIndexChanged.connect(self.setScoreIndex)
        self.__cb.activated.connect(self.edited)
        box.layout().addWidget(cb)

        self.layout().addWidget(box)

        box = QGroupBox(title=_tr.m[1247, "Number of features"], flat=True)
        self.__group = group = QButtonGroup(self, exclusive=True)
        self.__spins = {}

        form = QFormLayout()
        fixedrb = QRadioButton(_tr.m[1248, "Fixed:"], checked=True)
        group.addButton(fixedrb, UnivariateFeatureSelect.Fixed)
        kspin = QSpinBox(
            minimum=1, maximum=1000000, value=self.__k,
            enabled=self.__strategy == UnivariateFeatureSelect.Fixed
        )
        kspin.valueChanged[int].connect(self.setK)
        kspin.editingFinished.connect(self.edited)
        self.__spins[UnivariateFeatureSelect.Fixed] = kspin
        form.addRow(fixedrb, kspin)

        percrb = QRadioButton(_tr.m[1249, "Proportion:"])
        group.addButton(percrb, UnivariateFeatureSelect.Proportion)
        pspin = QDoubleSpinBox(
            minimum=1.0, maximum=100.0, singleStep=0.5,
            value=self.__p, suffix="%",
            enabled=self.__strategy == UnivariateFeatureSelect.Proportion
        )

        pspin.valueChanged[float].connect(self.setP)
        pspin.editingFinished.connect(self.edited)
        self.__spins[UnivariateFeatureSelect.Proportion] = pspin
        form.addRow(percrb, pspin)

#         form.addRow(QRadioButton("FDR"), QDoubleSpinBox())
#         form.addRow(QRadioButton("FPR"), QDoubleSpinBox())
#         form.addRow(QRadioButton("FWE"), QDoubleSpinBox())

        self.__group.buttonClicked.connect(self.__on_buttonClicked)
        box.setLayout(form)
        self.layout().addWidget(box)

    def setScoreIndex(self, scoreindex):
        if self.__scoreidx != scoreindex:
            self.__scoreidx = scoreindex
            self.__cb.setCurrentIndex(scoreindex)
            self.changed.emit()

    def scoreIndex(self):
        return self.__scoreidx

    def setStrategy(self, strategy):
        if self.__strategy != strategy:
            self.__strategy = strategy
            b = self.__group.button(strategy)
            b.setChecked(True)
            for st, rb in self.__spins.items():
                rb.setEnabled(st == strategy)
            self.changed.emit()

    def setK(self, k):
        if self.__k != k:
            self.__k = k
            spin = self.__spins[UnivariateFeatureSelect.Fixed]
            spin.setValue(k)
            if self.__strategy == UnivariateFeatureSelect.Fixed:
                self.changed.emit()

    def setP(self, p):
        if self.__p != p:
            self.__p = p
            spin = self.__spins[UnivariateFeatureSelect.Proportion]
            spin.setValue(p)
            if self.__strategy == UnivariateFeatureSelect.Proportion:
                self.changed.emit()

    def setItems(self, itemlist):
        for item in itemlist:
            self.__cb.addItem(item["text"])

    def __on_buttonClicked(self):
        strategy = self.__group.checkedId()
        self.setStrategy(strategy)
        self.edited.emit()

    def setParameters(self, params):
        score = params.get("score", 0)
        strategy = params.get("strategy", UnivariateFeatureSelect.Fixed)
        self.setScoreIndex(score)
        self.setStrategy(strategy)
        if strategy == UnivariateFeatureSelect.Fixed:
            self.setK(params.get("k", 10))
        else:
            self.setP(params.get("p", 75))

    def parameters(self):
        score = self.__scoreidx
        strategy = self.__strategy
        p = self.__p
        k = self.__k

        return {"score": score, "strategy": strategy, "p": p, "k": k}


class FeatureSelectEditor(BaseEditor):

    MEASURES = [
        (_tr.m[1250, "Information Gain"], preprocess.score.InfoGain),
        (_tr.m[1251, "Gain ratio"], preprocess.score.GainRatio),
        (_tr.m[1252, "Gini index"], preprocess.score.Gini),
        ("ReliefF", preprocess.score.ReliefF),
        (_tr.m[1253, "Fast Correlation Based Filter"], preprocess.score.FCBF),
        ("ANOVA", preprocess.score.ANOVA),
        ("Chi2", preprocess.score.Chi2),
        ("RReliefF", preprocess.score.RReliefF),
        (_tr.m[1254, "Univariate Linear Regression"], preprocess.score.UnivariateLinearRegression)
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.__score = 0
        self.__selecionidx = 0

        self.__uni_fs = UnivariateFeatureSelect()
        self.__uni_fs.setItems(
            [{"text": _tr.m[1255, "Information Gain"], "tooltip": ""},
             {"text": _tr.m[1256, "Gain Ratio"]},
             {"text": _tr.m[1257, "Gini Index"]},
             {"text": "ReliefF"},
             {"text": _tr.m[1258, "Fast Correlation Based Filter"]},
             {"text": "ANOVA"},
             {"text": "Chi2"},
             {"text": "RReliefF"},
             {"text": _tr.m[1259, "Univariate Linear Regression"]}
            ]
        )
        self.layout().addWidget(self.__uni_fs)
        self.__uni_fs.changed.connect(self.changed)
        self.__uni_fs.edited.connect(self.edited)

    def setParameters(self, params):
        self.__uni_fs.setParameters(params)

    def parameters(self):
        return self.__uni_fs.parameters()

    @staticmethod
    def createinstance(params):
        params = dict(params)
        score = params.pop("score", 0)
        score = FeatureSelectEditor.MEASURES[score][1]
        strategy = params.get("strategy", UnivariateFeatureSelect.Fixed)
        k = params.get("k", 10)
        p = params.get("p", 75.0)
        if strategy == UnivariateFeatureSelect.Fixed:
            return preprocess.fss.SelectBestFeatures(score(), k=k)
        elif strategy == UnivariateFeatureSelect.Proportion:
            return preprocess.fss.SelectBestFeatures(score(), k=p / 100)
        else:
            raise NotImplementedError

    def __repr__(self):
        params = self.__uni_fs.parameters()
        return _tr.m[1260, "Score: {}, Strategy (Fixed): {}"].format(
            self.MEASURES[params["score"]][0], params["k"])

# TODO: Model based FS (random forest variable importance, ...), RFE
# Unsupervised (min variance, constant, ...)??

class RandomFeatureSelectEditor(BaseEditor):
    #: Strategy
    Fixed, Percentage = 1, 2

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())

        self.__strategy = RandomFeatureSelectEditor.Fixed
        self.__k = 10
        self.__p = 75.0

        box = QGroupBox(title=_tr.m[1261, "Number of features"], flat=True)
        self.__group = group = QButtonGroup(self, exclusive=True)
        self.__spins = {}

        form = QFormLayout()
        fixedrb = QRadioButton(_tr.m[1262, "Fixed"], checked=True)
        group.addButton(fixedrb, RandomFeatureSelectEditor.Fixed)
        kspin = QSpinBox(
            minimum=1, maximum=1000000, value=self.__k,
            enabled=self.__strategy == RandomFeatureSelectEditor.Fixed
        )
        kspin.valueChanged[int].connect(self.setK)
        kspin.editingFinished.connect(self.edited)
        self.__spins[RandomFeatureSelectEditor.Fixed] = kspin
        form.addRow(fixedrb, kspin)

        percrb = QRadioButton(_tr.m[1263, "Percentage"])
        group.addButton(percrb, RandomFeatureSelectEditor.Percentage)
        pspin = QDoubleSpinBox(
            minimum=0.0, maximum=100.0, singleStep=0.5,
            value=self.__p, suffix="%",
            enabled=self.__strategy == RandomFeatureSelectEditor.Percentage
        )
        pspin.valueChanged[float].connect(self.setP)
        pspin.editingFinished.connect(self.edited)
        self.__spins[RandomFeatureSelectEditor.Percentage] = pspin
        form.addRow(percrb, pspin)

        self.__group.buttonClicked.connect(self.__on_buttonClicked)
        box.setLayout(form)
        self.layout().addWidget(box)

    def setStrategy(self, strategy):
        if self.__strategy != strategy:
            self.__strategy = strategy
            b = self.__group.button(strategy)
            b.setChecked(True)
            for st, rb in self.__spins.items():
                rb.setEnabled(st == strategy)
            self.changed.emit()

    def setK(self, k):
        if self.__k != k:
            self.__k = k
            spin = self.__spins[RandomFeatureSelectEditor.Fixed]
            spin.setValue(k)
            if self.__strategy == RandomFeatureSelectEditor.Fixed:
                self.changed.emit()

    def setP(self, p):
        if self.__p != p:
            self.__p = p
            spin = self.__spins[RandomFeatureSelectEditor.Percentage]
            spin.setValue(p)
            if self.__strategy == RandomFeatureSelectEditor.Percentage:
                self.changed.emit()

    def __on_buttonClicked(self):
        strategy = self.__group.checkedId()
        self.setStrategy(strategy)
        self.edited.emit()

    def setParameters(self, params):
        strategy = params.get("strategy", RandomFeatureSelectEditor.Fixed)
        self.setStrategy(strategy)
        if strategy == RandomFeatureSelectEditor.Fixed:
            self.setK(params.get("k", 10))
        else:
            self.setP(params.get("p", 75.0))

    def parameters(self):
        strategy = self.__strategy
        p = self.__p
        k = self.__k

        return {"strategy": strategy, "p": p, "k": k}

    @staticmethod
    def createinstance(params):
        params = dict(params)
        strategy = params.get("strategy", RandomFeatureSelectEditor.Fixed)
        k = params.get("k", 10)
        p = params.get("p", 75.0)
        if strategy == RandomFeatureSelectEditor.Fixed:
            return preprocess.fss.SelectRandomFeatures(k=k)
        elif strategy == RandomFeatureSelectEditor.Percentage:
            return preprocess.fss.SelectRandomFeatures(k=p/100)
        else:
            # further implementations
            raise NotImplementedError

    def __repr__(self):
        if self.__strategy == self.Fixed:
            # private attributes may not appear translated strings
            num = self.__k
            return _tr.e(_tr.c(1264, f"select {num} {pl(num,'feature')}"))
        else:
            perc = self.__p
            return _tr.e(_tr.c(1265, f"select {perc} % features"))


def index_to_enum(enum, i):
    """Enums, by default, are not int-comparable, so use an ad-hoc mapping of
    int to enum value at that position"""
    return list(enum)[i]


def enum_to_index(enum, key):
    """Enums, by default, are not int-comparable, so use an ad-hoc mapping of
    enum key to its int position"""
    return list(enum).index(key)

class Scale(BaseEditor):
    CenterByMean, ScaleBySD, NormalizeBySD, NormalizeBySpan_ZeroBased, \
        NormalizeSpan_NonZeroBased = 0, 1, 2, 3, 4

    Names = {
        NormalizeBySD: _tr.m[1266, "Standardize to μ=0, σ²=1"],
        CenterByMean: _tr.m[1267, "Center to μ=0"],
        ScaleBySD: _tr.m[1268, "Scale to σ²=1"],
        NormalizeSpan_NonZeroBased: _tr.m[1269, "Normalize to interval [-1, 1]"],
        NormalizeBySpan_ZeroBased: _tr.m[1270, "Normalize to interval [0, 1]"],
    }

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())

        self.__method = Scale.NormalizeBySD
        self.__group = group = QButtonGroup(self, exclusive=True)
        group.buttonClicked.connect(self.__on_buttonClicked)

        for methodid in [self.NormalizeBySD, self.CenterByMean, self.ScaleBySD,
                         self.NormalizeSpan_NonZeroBased,
                         self.NormalizeBySpan_ZeroBased]:
            text = self.Names[methodid]
            rb = QRadioButton(text=text, checked=self.__method == methodid)
            group.addButton(rb, methodid)
            self.layout().addWidget(rb)

    def setMethod(self, method):
        b = self.__group.button(method)
        if b is not None:
            b.setChecked(True)
            self.__method = method
            self.changed.emit()

    def setParameters(self, params):
        method = params.get("method", Scale.NormalizeBySD)
        self.setMethod(method)

    def parameters(self):
        return {"method": self.__method}

    def __on_buttonClicked(self):
        self.__method = self.__group.checkedId()
        self.changed.emit()
        self.edited.emit()

    @staticmethod
    def createinstance(params):
        method = params.get("method", Scale.NormalizeBySD)
        if method == Scale.CenterByMean:
            return _Scale(_Scale.CenteringType.Mean,
                          _Scale.ScalingType.NoScaling)
        elif method == Scale.ScaleBySD:
            return _Scale(_Scale.CenteringType.NoCentering,
                          _Scale.ScalingType.Std)
        elif method == Scale.NormalizeBySD:
            return Normalize(norm_type=Normalize.NormalizeBySD)
        elif method == Scale.NormalizeBySpan_ZeroBased:
            return Normalize(norm_type=Normalize.NormalizeBySpan)
        else:  # method == Scale.NormalizeSpan_NonZeroBased
            return Normalize(norm_type=Normalize.NormalizeBySpan,
                             zero_based=False)

    def __repr__(self):
        return self.Names[self.__method]


class Randomize(BaseEditor):
    RandomizeClasses, RandomizeAttributes, RandomizeMetas = _Randomize.Type

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())

        form = QFormLayout()
        self.__rand_type_cb = QComboBox()
        self.__rand_type_cb.addItems([_tr.m[1271, "Classes"],
                                      _tr.m[1272, "Features"],
                                      _tr.m[1273, "Meta data"]])

        self.__rand_type_cb.currentIndexChanged.connect(self.changed)
        self.__rand_type_cb.activated.connect(self.edited)

        self.__rand_seed_ch = QCheckBox()
        self.__rand_seed_ch.clicked.connect(self.edited)

        form.addRow(_tr.m[1274, "Randomize:"], self.__rand_type_cb)
        form.addRow(_tr.m[1275, "Replicable shuffling:"], self.__rand_seed_ch)
        self.layout().addLayout(form)

    def setParameters(self, params):
        rand_type = params.get("rand_type", Randomize.RandomizeClasses)
        self.__rand_type_cb.setCurrentIndex(
            enum_to_index(_Randomize.Type, rand_type))
        self.__rand_seed_ch.setChecked(params.get("rand_seed", 1) or 0)

    def parameters(self):
        return {"rand_type": index_to_enum(_Randomize.Type,
                                           self.__rand_type_cb.currentIndex()),
                "rand_seed": 1 if self.__rand_seed_ch.isChecked() else None}

    @staticmethod
    def createinstance(params):
        rand_type = params.get("rand_type", Randomize.RandomizeClasses)
        rand_seed = params.get("rand_seed", 1)
        return _Randomize(rand_type=rand_type, rand_seed=rand_seed)

    def __repr__(self):
        return "{}, {}".format(self.__rand_type_cb.currentText(),
                               _tr.m[1276, "Replicable"] if self.__rand_seed_ch.isChecked()
                               else _tr.m[1277, "Not replicable"])


class PCA(BaseEditor):

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())

        self.n_components = 10

        form = QFormLayout()
        self.cspin = QSpinBox(minimum=1, value=self.n_components)
        self.cspin.valueChanged[int].connect(self.setC)
        self.cspin.editingFinished.connect(self.edited)

        form.addRow(_tr.m[1278, "Components:"], self.cspin)
        self.layout().addLayout(form)

    def setParameters(self, params):
        self.n_components = params.get("n_components", 10)

    def parameters(self):
        return {"n_components": self.n_components}

    def setC(self, n_components):
        if self.n_components != n_components:
            self.n_components = n_components
            self.cspin.setValue(n_components)
            self.changed.emit()

    @staticmethod
    def createinstance(params):
        n_components = params.get("n_components", 10)
        return ProjectPCA(n_components=n_components)

    def __repr__(self):
        return _tr.m[1279, "Components: {}"].format(self.cspin.value())


class CUR(BaseEditor):

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())

        self.rank = 10
        self.max_error = 1

        form = QFormLayout()
        self.rspin = QSpinBox(minimum=2, maximum=1000000, value=self.rank)
        self.rspin.valueChanged[int].connect(self.setR)
        self.rspin.editingFinished.connect(self.edited)
        self.espin = QDoubleSpinBox(
            minimum=0.1, maximum=100.0, singleStep=0.1,
            value=self.max_error)
        self.espin.valueChanged[float].connect(self.setE)
        self.espin.editingFinished.connect(self.edited)

        form.addRow(_tr.m[1280, "Rank:"], self.rspin)
        form.addRow(_tr.m[1281, "Relative error:"], self.espin)
        self.layout().addLayout(form)

    def setParameters(self, params):
        self.setR(params.get("rank", 10))
        self.setE(params.get("max_error", 1))

    def parameters(self):
        return {"rank": self.rank, "max_error": self.max_error}

    def setR(self, rank):
        if self.rank != rank:
            self.rank = rank
            self.rspin.setValue(rank)
            self.changed.emit()

    def setE(self, max_error):
        if self.max_error != max_error:
            self.max_error = max_error
            self.espin.setValue(max_error)
            self.changed.emit()

    @staticmethod
    def createinstance(params):
        rank = params.get("rank", 10)
        max_error = params.get("max_error", 1)
        return ProjectCUR(rank=rank, max_error=max_error)

    def __repr__(self):
        return _tr.m[1282, "Rank: {}, Relative error: {}"].format(self.rspin.value(),
                                                     self.espin.value())


# This is intended for future improvements.
# I.e. it should be possible to add/register preprocessor actions
# through entry points (for use by add-ons). Maybe it should be a
# general framework (this is not the only place where such
# functionality is desired (for instance in Orange v2.* Rank widget
# already defines its own entry point).
class Description:
    """
    A description of an action/function.
    """
    def __init__(self, title, icon=None, summary=None, input_=None, output=None,
                 requires=None, note=None, related=None, keywords=None,
                 helptopic=None):
        self.title = title
        self.icon = icon
        self.summary = summary
        self.input = input_
        self.output = output
        self.requires = requires
        self.note = note
        self.related = related
        self.keywords = keywords
        self.helptopic = helptopic


class PreprocessAction:
    def __init__(self, name, qualname, category, description, viewclass):
        self.name = name
        self.qualname = qualname
        self.category = category
        self.description = description
        self.viewclass = viewclass


def icon_path(basename):
    path = importlib.resources.files(__package__).joinpath("icons/" + basename)
    return str(path)


PREPROCESS_ACTIONS = [
    PreprocessAction(
        _tr.m[1283, "Discretize"], "orange.preprocess.discretize", _tr.m[1284, "Discretization"],
        Description(_tr.m[1285, "Discretize Continuous Variables"],
                    icon_path("Discretize.svg")),
        DiscretizeEditor
    ),
    PreprocessAction(
        _tr.m[1286, "Continuize"], "orange.preprocess.continuize", _tr.m[1287, "Continuization"],
        Description(_tr.m[1288, "Continuize Discrete Variables"],
                    icon_path("Continuize.svg")),
        ContinuizeEditor
    ),
    PreprocessAction(
        _tr.m[1289, "Impute"], "orange.preprocess.impute", _tr.m[1290, "Impute"],
        Description(_tr.m[1291, "Impute Missing Values"],
                    icon_path("Impute.svg")),
        ImputeEditor
    ),
    PreprocessAction(
        _tr.m[1292, "Feature Selection"], "orange.preprocess.fss", _tr.m[1293, "Feature Selection"],
        Description(_tr.m[1294, "Select Relevant Features"],
                    icon_path("SelectColumns.svg")),
        FeatureSelectEditor
    ),
    PreprocessAction(
        _tr.m[1295, "Random Feature Selection"], "orange.preprocess.randomfss",
        _tr.m[1296, "Random Feature Selection"],
        Description(_tr.m[1297, "Select Random Features"],
                    icon_path("SelectColumnsRandom.svg")),
        RandomFeatureSelectEditor
    ),
    PreprocessAction(
        _tr.m[1298, "Normalize"], "orange.preprocess.scale", _tr.m[1299, "Scale"],
        Description(_tr.m[1300, "Normalize Features"],
                    icon_path("Normalize.svg")),
        Scale
    ),
    PreprocessAction(
        _tr.m[1301, "Randomize"], "orange.preprocess.randomize", _tr.m[1302, "Randomization"],
        Description(_tr.m[1303, "Randomize"],
                    icon_path("Random.svg")),
        Randomize
    ),
    PreprocessAction(
        _tr.m[1304, "Remove Sparse"], "orange.preprocess.remove_sparse", _tr.m[1305, "Feature Selection"],
        Description(_tr.m[1306, "Remove Sparse Features"],
                    icon_path("PurgeDomain.svg")),
        RemoveSparseEditor
    ),
    PreprocessAction(
        "PCA", "orange.preprocess.pca", "PCA",
        Description(_tr.m[1307, "Principal Component Analysis"],
                    icon_path("PCA.svg")),
        PCA
    ),
    PreprocessAction(
        _tr.m[1308, "CUR"], "orange.preprocess.cur", _tr.m[1309, "CUR"],
        Description(_tr.m[1310, "CUR Matrix Decomposition"],
                    icon_path("SelectColumns.svg")),
        CUR
    )
]


# TODO: Extend with entry points here
# PREPROCESS_ACTIONS += iter_entry_points("Orange.widgets.data.owpreprocess")

# ####
# The actual owwidget
# ####

# Note:
# The preprocessors are drag/dropped onto a sequence widget, where
# they can be reordered/removed/edited.
#
# Model <-> Adapter/Controller <-> View
#
# * `Model`: the current constructed preprocessor model.
# * the source (of drag/drop) is an item model displayed in a list
#   view (source list).
# * the drag/drop is controlled by the controller/adapter,


class OWPreprocess(widget.OWWidget, openclass=True):
    name = _tr.m[1311, "Preprocess"]
    description = _tr.m[1312, "Construct a data preprocessing pipeline."]
    category = _tr.m[1313, "Transform"]
    icon = "icons/Preprocess.svg"
    priority = 2100
    keywords = _tr.m[1314, "preprocess, process"]

    settings_version = 2

    class Inputs:
        data = Input(_tr.m[1315, "Data"], Orange.data.Table)

    class Outputs:
        preprocessor = Output(_tr.m[1316, "Preprocessor"], preprocess.preprocess.Preprocess, dynamic=False)
        preprocessed_data = Output(_tr.m[1317, "Preprocessed Data"], Orange.data.Table)

    storedsettings = Setting({})
    autocommit = Setting(True)
    PREPROCESSORS = PREPROCESS_ACTIONS
    CONTROLLER = Controller

    def __init__(self):
        super().__init__()

        self.data = None
        self._invalidated = False

        # List of available preprocessors (DescriptionRole : Description)
        self.preprocessors = QStandardItemModel()

        def mimeData(indexlist):
            assert len(indexlist) == 1
            index = indexlist[0]
            qname = index.data(DescriptionRole).qualname
            m = QMimeData()
            m.setData("application/x-qwidget-ref", qname.encode("utf-8"))
            return m
        # TODO: Fix this (subclass even if just to pass a function
        # for mimeData delegate)
        self.preprocessors.mimeData = mimeData

        box = gui.vBox(self.controlArea, _tr.m[1318, "Preprocessors"])
        gui.rubber(self.controlArea)

        # we define a class that lets us set the vertical sizeHint
        # based on the height and number of items in the list
        # see self.__update_list_sizeHint

        class ListView(QListView):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.vertical_hint = None

            def sizeHint(self):
                sh = super().sizeHint()
                if self.vertical_hint:
                    return QSize(sh.width(), self.vertical_hint)
                return sh

        self.preprocessorsView = view = ListView(
            selectionMode=QListView.SingleSelection,
            dragEnabled=True,
            dragDropMode=QListView.DragOnly
        )
        view.setModel(self.preprocessors)
        view.activated.connect(self.__activated)

        box.layout().addWidget(view)

        ####
        self._qname2ppdef = {ppdef.qualname: ppdef for
                             ppdef in self.PREPROCESSORS}

        # List of 'selected' preprocessors and their parameters.
        self.preprocessormodel = None

        self.flow_view = SequenceFlow()
        self.controler = self.CONTROLLER(self.flow_view, parent=self)

        self.overlay = OverlayWidget(self)
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay.setWidget(self.flow_view)
        self.overlay.setLayout(QVBoxLayout())
        self.overlay.layout().addWidget(
            QLabel(_tr.m[1319, "Drag items from the list on the left"], wordWrap=True))

        self.scroll_area = QScrollArea(
            verticalScrollBarPolicy=Qt.ScrollBarAlwaysOn
        )
        self.scroll_area.viewport().setAcceptDrops(True)
        self.scroll_area.setWidget(self.flow_view)
        self.scroll_area.setWidgetResizable(True)
        self.mainArea.layout().addWidget(self.scroll_area)
        self.flow_view.installEventFilter(self)

        gui.auto_apply(self.buttonsArea, self, "autocommit")

        self.__update_size_constraint_timer = QTimer(
            self, singleShot=True, interval=0,
        )
        self.__update_size_constraint_timer.timeout.connect(self.__update_size_constraint)
        self._initialize()

    def _initialize(self):
        for pp_def in self.PREPROCESSORS:
            description = pp_def.description
            if description.icon:
                icon = QIcon(description.icon)
            else:
                icon = QIcon()
            item = QStandardItem(icon, description.title)
            item.setToolTip(description.summary or "")
            item.setData(pp_def, DescriptionRole)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable |
                          Qt.ItemIsDragEnabled)
            self.preprocessors.appendRow([item])

        self.__update_list_sizeHint()

        model = self.load(self.storedsettings)

        self.set_model(model)

        if not model.rowCount():
            # enforce default width constraint if no preprocessors
            # are instantiated (if the model is not empty the constraints
            # will be triggered by LayoutRequest event on the `flow_view`)
            self.__update_size_constraint()

        self.apply()

    def __update_list_sizeHint(self):
        view = self.preprocessorsView

        h = view.sizeHintForRow(0)
        n = self.preprocessors.rowCount()
        view.vertical_hint = n * h + 2  # only on Mac?
        view.updateGeometry()

    def load(self, saved):
        """Load a preprocessor list from a dict."""
        preprocessors = saved.get("preprocessors", [])
        model = StandardItemModel()

        def dropMimeData(data, action, row, _column, _parent):
            if data.hasFormat("application/x-qwidget-ref") and \
                    action == Qt.CopyAction:
                qname = bytes(data.data("application/x-qwidget-ref")).decode()

                ppdef = self._qname2ppdef[qname]
                item = QStandardItem(ppdef.description.title)
                item.setData({}, ParametersRole)
                item.setData(ppdef.description.title, Qt.DisplayRole)
                item.setData(ppdef, DescriptionRole)
                self.preprocessormodel.insertRow(row, [item])
                return True
            else:
                return False

        model.dropMimeData = dropMimeData

        for qualname, params in preprocessors:
            pp_def = self._qname2ppdef[qualname]
            description = pp_def.description
            item = QStandardItem(description.title)
            if description.icon:
                icon = QIcon(description.icon)
            else:
                icon = QIcon()
            item.setIcon(icon)
            item.setToolTip(description.summary)
            item.setData(pp_def, DescriptionRole)
            item.setData(params, ParametersRole)

            model.appendRow(item)
        return model

    @staticmethod
    def save(model):
        """Save the preprocessor list to a dict."""
        d = {"name": ""}
        preprocessors = []
        for i in range(model.rowCount()):
            item = model.item(i)
            pp_def = item.data(DescriptionRole)
            params = item.data(ParametersRole)
            preprocessors.append((pp_def.qualname, params))

        d["preprocessors"] = preprocessors
        return d


    def set_model(self, ppmodel):
        if self.preprocessormodel:
            self.preprocessormodel.dataChanged.disconnect(self.__on_modelchanged)
            self.preprocessormodel.rowsInserted.disconnect(self.__on_modelchanged)
            self.preprocessormodel.rowsRemoved.disconnect(self.__on_modelchanged)
            self.preprocessormodel.rowsMoved.disconnect(self.__on_modelchanged)
            self.preprocessormodel.deleteLater()

        self.preprocessormodel = ppmodel
        self.controler.setModel(ppmodel)
        if ppmodel is not None:
            self.preprocessormodel.dataChanged.connect(self.__on_modelchanged)
            self.preprocessormodel.rowsInserted.connect(self.__on_modelchanged)
            self.preprocessormodel.rowsRemoved.connect(self.__on_modelchanged)
            self.preprocessormodel.rowsMoved.connect(self.__on_modelchanged)

        self.__update_overlay()

    def __update_overlay(self):
        if self.preprocessormodel is None or \
                self.preprocessormodel.rowCount() == 0:
            self.overlay.setWidget(self.flow_view)
            self.overlay.show()
        else:
            self.overlay.setWidget(None)
            self.overlay.hide()

    def __on_modelchanged(self):
        self.__update_overlay()
        self.commit.deferred()

    @Inputs.data
    @check_sql_input
    def set_data(self, data=None):
        """Set the input dataset."""
        self.data = data

    def handleNewSignals(self):
        self.apply()

    def __activated(self, index):
        item = self.preprocessors.itemFromIndex(index)
        action = item.data(DescriptionRole)
        item = QStandardItem()
        item.setData({}, ParametersRole)
        item.setData(action.description.title, Qt.DisplayRole)
        item.setData(action, DescriptionRole)
        self.preprocessormodel.appendRow([item])

    def buildpreproc(self):
        plist = []
        for i in range(self.preprocessormodel.rowCount()):
            item = self.preprocessormodel.item(i)
            desc = item.data(DescriptionRole)
            params = item.data(ParametersRole)

            if not isinstance(params, dict):
                params = {}

            create = desc.viewclass.createinstance
            plist.append(create(params))

        if len(plist) == 1:
            return plist[0]
        else:
            return preprocess.preprocess.PreprocessorList(plist)

    def apply(self):
        # Sync the model into storedsettings on every apply.
        self.storeSpecificSettings()
        preprocessor = self.buildpreproc()

        if self.data is not None:
            self.error()
            try:
                data = preprocessor(self.data)
            except (ValueError, ZeroDivisionError) as e:
                self.error(str(e))
                return
        else:
            data = None

        self.Outputs.preprocessor.send(preprocessor)
        self.Outputs.preprocessed_data.send(data)

    @gui.deferred
    def commit(self):
        if not self._invalidated:
            self._invalidated = True
            QApplication.postEvent(self, QEvent(QEvent.User))

    def customEvent(self, event):
        if event.type() == QEvent.User and self._invalidated:
            self._invalidated = False
            self.apply()

    def eventFilter(self, receiver, event):
        if receiver is self.flow_view and event.type() == QEvent.LayoutRequest:
            self.__update_size_constraint_timer.start()
        return super().eventFilter(receiver, event)

    def storeSpecificSettings(self):
        """Reimplemented."""
        self.storedsettings = self.save(self.preprocessormodel)
        super().storeSpecificSettings()

    def saveSettings(self):
        """Reimplemented."""
        self.storedsettings = self.save(self.preprocessormodel)
        super().saveSettings()

    @classmethod
    def migrate_settings(cls, settings, version):
        if version < 2:
            for action, params in settings["storedsettings"]["preprocessors"]:
                if action == "orange.preprocess.scale":
                    scale = center = None
                    if "center" in params:
                        center = params.pop("center").name
                    if "scale" in params:
                        scale = params.pop("scale").name
                    migratable = {
                        ("Mean", "NoScaling"): Scale.CenterByMean,
                        ("NoCentering", "Std"): Scale.ScaleBySD,
                        ("Mean", "Std"): Scale.NormalizeBySD,
                        ("NoCentering", "Span"): Scale.NormalizeBySpan_ZeroBased
                    }
                    params["method"] = \
                        migratable.get((center, scale), Scale.NormalizeBySD)

    def onDeleteWidget(self):
        self.data = None
        self.set_model(None)
        super().onDeleteWidget()

    @Slot()
    def __update_size_constraint(self):
        # Update minimum width constraint on the scroll area containing
        # the 'instantiated' preprocessor list (to avoid the horizontal
        # scroll bar).
        sh = self.flow_view.minimumSizeHint()
        scroll_width = self.scroll_area.verticalScrollBar().width()
        self.scroll_area.setMinimumWidth(
            min(max(sh.width() + scroll_width + 2, self.controlArea.width()),
                520))

    def send_report(self):
        pp = [(self.controler.model().index(i, 0).data(Qt.DisplayRole), w)
              for i, w in enumerate(self.controler.view.widgets())]
        if pp:
            self.report_items(_tr.m[1320, "Settings"], pp)

if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWPreprocess).run(Orange.data.Table("brown-selected"))
