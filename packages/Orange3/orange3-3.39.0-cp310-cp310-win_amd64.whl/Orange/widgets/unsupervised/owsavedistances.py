from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from Orange.widgets.widget import Input, Msg
from Orange.misc import DistMatrix
from Orange.widgets.utils.save.owsavebase import OWSaveBase
from Orange.widgets.utils.widgetpreview import WidgetPreview


class OWSaveDistances(OWSaveBase):
    name = _tr.m[3021, "Save Distance Matrix"]
    description = _tr.m[3022, "Save distance matrix to an output file."]
    icon = "icons/SaveDistances.svg"
    keywords = _tr.m[3023, "save distance matrix, distance matrix, save"]

    filters = [_tr.m[3024, "Excel File (*.xlsx)"], _tr.m[3025, "Distance File (*.dst)"]]

    class Warning(OWSaveBase.Warning):
        table_not_saved = Msg(_tr.m[3026, "Associated data was not saved."])
        part_not_saved = Msg(_tr.m[3027, "Data associated with {} was not saved."])

    class Inputs:
        distances = Input(_tr.m[3028, "Distances"], DistMatrix)

    @Inputs.distances
    def set_distances(self, data):
        self.data = data
        self.on_new_input()

    def do_save(self):
        dist = self.data
        dist.save(self.filename)
        skip_row = not dist.has_row_labels() and dist.row_items is not None
        skip_col = not dist.has_col_labels() and dist.col_items is not None
        self.Warning.table_not_saved(shown=skip_row and skip_col)
        self.Warning.part_not_saved(_tr.m[3029, "columns"] if skip_col else _tr.m[3030, "rows"],
                                    shown=skip_row != skip_col,)

    def send_report(self):
        self.report_items((
            (_tr.m[3031, "Input"], _tr.m[3032, "none"] if self.data is None else self._description()),
            (_tr.m[3033, "File name"], self.filename or _tr.m[3034, "not set"])))

    def _description(self):
        dist = self.data
        labels = _tr.m[3035, " and "].join(
            filter(None, (dist.row_items is not None and _tr.m[3036, "row"],
                          dist.col_items is not None and _tr.m[3037, "column"])))
        if labels:
            labels = _tr.e(_tr.c(3038, f"; {labels} labels"))
        return _tr.e(_tr.c(3039, f"{len(dist)}-dimensional matrix{labels}"))


if __name__ == "__main__":
    from Orange.data import Table
    from Orange.distance import Euclidean
    WidgetPreview(OWSaveDistances).run(Euclidean(Table("iris")))
