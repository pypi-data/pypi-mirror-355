from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from typing import List

from Orange.base import Learner
from Orange.data import Table
from Orange.ensembles.stack import StackedFitter
from Orange.widgets.settings import Setting
from Orange.widgets.utils.owlearnerwidget import OWBaseLearner
from Orange.widgets.widget import Input, MultiInput


class OWStackedLearner(OWBaseLearner):
    name = _tr.m[2479, "Stacking"]
    description = _tr.m[2480, "Stack multiple models."]
    icon = "icons/Stacking.svg"
    priority = 100

    LEARNER = StackedFitter

    learner_name = Setting(_tr.m[2481, "Stack"])

    class Inputs(OWBaseLearner.Inputs):
        learners = MultiInput(_tr.m[2482, "Learners"], Learner, filter_none=True)
        aggregate = Input(_tr.m[2483, "Aggregate"], Learner)

    def __init__(self):
        self.learners: List[Learner] = []
        self.aggregate = None
        super().__init__()

    def add_main_layout(self):
        pass

    @Inputs.learners
    def set_learner(self, index: int, learner: Learner):
        self.learners[index] = learner
        self._invalidate()

    @Inputs.learners.insert
    def insert_learner(self, index, learner):
        self.learners.insert(index, learner)
        self._invalidate()

    @Inputs.learners.remove
    def remove_learner(self, index):
        self.learners.pop(index)
        self._invalidate()

    @Inputs.aggregate
    def set_aggregate(self, aggregate):
        self.aggregate = aggregate
        self._invalidate()

    def _invalidate(self):
        self.learner = self.model = None
        # ... and handleNewSignals will do the rest

    def create_learner(self):
        if not self.learners:
            return None
        return self.LEARNER(
            tuple(self.learners), aggregate=self.aggregate,
            preprocessors=self.preprocessors)

    def get_learner_parameters(self):
        return ((_tr.m[2484, "Base learners"], [l.name for l in self.learners]),
                (_tr.m[2485, "Aggregator"],
                 self.aggregate.name if self.aggregate else _tr.m[2486, 'default']))


if __name__ == "__main__":
    import sys
    from AnyQt.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = OWStackedLearner()
    d = Table(sys.argv[1] if len(sys.argv) > 1 else 'iris')
    ow.set_data(d)
    ow.show()
    a.exec()
    ow.saveSettings()
