from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from AnyQt.QtWidgets import QFrame

from Orange.data import Table
from Orange.preprocess.remove import Remove
from Orange.widgets import gui, widget
from Orange.widgets.settings import Setting
from Orange.widgets.utils.sql import check_sql_input
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import Input, Output


class OWPurgeDomain(widget.OWWidget):
    name = _tr.m[1321, "Purge Domain"]
    description = (_tr.m[1322, "Remove redundant values and features from the dataset. "] + _tr.m[1323, "Sort values."])
    icon = "icons/PurgeDomain.svg"
    category = _tr.m[1324, "Transform"]
    keywords = _tr.m[1325, "remove, delete, unused"]
    priority = 2210

    class Inputs:
        data = Input(_tr.m[1326, "Data"], Table)

    class Outputs:
        data = Output(_tr.m[1327, "Data"], Table)

    removeValues = Setting(1)
    removeAttributes = Setting(1)
    removeClasses = Setting(1)
    removeClassAttribute = Setting(1)
    removeMetaAttributeValues = Setting(1)
    removeMetaAttributes = Setting(1)
    autoSend = Setting(True)
    sortValues = Setting(True)
    sortClasses = Setting(True)

    want_main_area = False
    resizing_enabled = False

    feature_options = (('sortValues', _tr.m[1328, 'Sort categorical feature values']),
                       ('removeValues', _tr.m[1329, 'Remove unused feature values']),
                       ('removeAttributes', _tr.m[1330, 'Remove constant features']))

    class_options = (('sortClasses', _tr.m[1331, 'Sort categorical class values']),
                     ('removeClasses', _tr.m[1332, 'Remove unused class variable values']),
                     ('removeClassAttribute', _tr.m[1333, 'Remove constant class variables']))

    meta_options = (('removeMetaAttributeValues', _tr.m[1334, 'Remove unused meta attribute values']),
                    ('removeMetaAttributes', _tr.m[1335, 'Remove constant meta attributes']))

    stat_labels = ((_tr.m[1336, 'Sorted features'], 'resortedAttrs'),
                   (_tr.m[1337, 'Reduced features'], 'reducedAttrs'),
                   (_tr.m[1338, 'Removed features'], 'removedAttrs'),
                   (_tr.m[1339, 'Sorted classes'], 'resortedClasses'),
                   (_tr.m[1340, 'Reduced classes'], 'reducedClasses'),
                   (_tr.m[1341, 'Removed classes'], 'removedClasses'),
                   (_tr.m[1342, 'Reduced metas'], 'reducedMetas'),
                   (_tr.m[1343, 'Removed metas'], 'removedMetas'))

    def __init__(self):
        super().__init__()
        self.data = None

        self.removedAttrs = "-"
        self.reducedAttrs = "-"
        self.resortedAttrs = "-"
        self.removedClasses = "-"
        self.reducedClasses = "-"
        self.resortedClasses = "-"
        self.removedMetas = "-"
        self.reducedMetas = "-"

        def add_line(parent):
            frame = QFrame()
            frame.setFrameShape(QFrame.HLine)
            frame.setFrameShadow(QFrame.Sunken)
            parent.layout().addWidget(frame)

        boxAt = gui.vBox(self.controlArea, _tr.m[1344, "Features"])
        for value, label in self.feature_options:
            gui.checkBox(boxAt, self, value, label,
                         callback=self.commit.deferred)
        add_line(boxAt)
        gui.label(boxAt, self,
                  (_tr.m[1345, "Sorted: %(resortedAttrs)s, "] + _tr.m[1346, "reduced: %(reducedAttrs)s, removed: %(removedAttrs)s"]))

        boxAt = gui.vBox(self.controlArea, _tr.m[1347, "Classes"])
        for value, label in self.class_options:
            gui.checkBox(boxAt, self, value, label,
                         callback=self.commit.deferred)
        add_line(boxAt)
        gui.label(boxAt, self,
                  (_tr.m[1348, "Sorted: %(resortedClasses)s,"] + _tr.m[1349, "reduced: %(reducedClasses)s, removed: %(removedClasses)s"]))

        boxAt = gui.vBox(self.controlArea, _tr.m[1350, "Meta attributes"])
        for value, label in self.meta_options:
            gui.checkBox(boxAt, self, value, label,
                         callback=self.commit.deferred)
        add_line(boxAt)
        gui.label(boxAt, self,
                  _tr.m[1351, "Reduced: %(reducedMetas)s, removed: %(removedMetas)s"])

        gui.auto_send(self.buttonsArea, self, "autoSend")

    @Inputs.data
    @check_sql_input
    def setData(self, dataset):
        if dataset is not None:
            self.data = dataset
            self.commit.now()
        else:
            self.removedAttrs = "-"
            self.reducedAttrs = "-"
            self.resortedAttrs = "-"
            self.removedClasses = "-"
            self.reducedClasses = "-"
            self.resortedClasses = "-"
            self.removedMetas = "-"
            self.reducedMetas = "-"
            self.Outputs.data.send(None)
            self.data = None

    @gui.deferred
    def commit(self):
        if self.data is None:
            return

        attr_flags = sum([Remove.SortValues * self.sortValues,
                          Remove.RemoveConstant * self.removeAttributes,
                          Remove.RemoveUnusedValues * self.removeValues])
        class_flags = sum([Remove.SortValues * self.sortClasses,
                           Remove.RemoveConstant * self.removeClassAttribute,
                           Remove.RemoveUnusedValues * self.removeClasses])
        meta_flags = sum([Remove.RemoveConstant * self.removeMetaAttributes,
                          Remove.RemoveUnusedValues * self.removeMetaAttributeValues])
        remover = Remove(attr_flags, class_flags, meta_flags)
        cleaned = remover(self.data)
        attr_res, class_res, meta_res = \
            remover.attr_results, remover.class_results, remover.meta_results

        self.removedAttrs = attr_res['removed']
        self.reducedAttrs = attr_res['reduced']
        self.resortedAttrs = attr_res['sorted']

        self.removedClasses = class_res['removed']
        self.reducedClasses = class_res['reduced']
        self.resortedClasses = class_res['sorted']

        self.removedMetas = meta_res['removed']
        self.reducedMetas = meta_res['reduced']

        self.Outputs.data.send(cleaned)

    def send_report(self):
        def list_opts(opts):
            return "; ".join(label.lower()
                             for value, label in opts
                             if getattr(self, value)) or _tr.m[1352, "no changes"]

        self.report_items(_tr.m[1353, "Settings"], (
            (_tr.m[1354, "Features"], list_opts(self.feature_options)),
            (_tr.m[1355, "Classes"], list_opts(self.class_options)),
            (_tr.m[1356, "Metas"], list_opts(self.meta_options))))
        if self.data:
            self.report_items(_tr.m[1357, "Statistics"], (
                (label, getattr(self, value))
                for label, value in self.stat_labels
            ))


if __name__ == "__main__":  # pragma: no cover
    data = Table.from_url("https://datasets.biolab.si/core/car.tab")
    subset = [inst for inst in data if inst["buying"] == "v-high"]
    subset = Table(data.domain, subset)
    # The "buying" should be removed and the class "y" reduced
    WidgetPreview(OWPurgeDomain).run(subset)
