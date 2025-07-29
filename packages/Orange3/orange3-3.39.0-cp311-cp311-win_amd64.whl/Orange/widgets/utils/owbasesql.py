from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from typing import Type
from collections import OrderedDict

from AnyQt.QtWidgets import QLineEdit, QSizePolicy

from Orange.data import Table
from Orange.data.sql.backend import Backend
from Orange.data.sql.backend.base import BackendError
from Orange.widgets import gui, report
from Orange.widgets.credentials import CredentialManager
from Orange.widgets.settings import Setting
from Orange.widgets.utils.signals import Output
from Orange.widgets.widget import OWWidget, Msg


class OWBaseSql(OWWidget, openclass=True):
    """Base widget for connecting to a database.
    Override `get_backend` when subclassing to get corresponding backend.
    """
    class Outputs:
        data = Output(_tr.m[3193, "Data"], Table)

    class Error(OWWidget.Error):
        connection = Msg("{}")

    want_main_area = False
    resizing_enabled = False

    host = Setting(None)  # type: Optional[str]
    port = Setting(None)  # type: Optional[str]
    database = Setting(None)  # type: Optional[str]
    schema = Setting(None)  # type: Optional[str]
    username = ""
    password = ""

    def __init__(self):
        super().__init__()
        self.backend = None  # type: Optional[Backend]
        self.data_desc_table = None  # type: Optional[Table]
        self.database_desc = None  # type: Optional[OrderedDict]
        self._setup_gui()
        self.connect()

    def _setup_gui(self):
        self.controlArea.setMinimumWidth(360)

        vbox = gui.vBox(self.controlArea, _tr.m[3194, "Server"])
        self.serverbox = gui.vBox(vbox)
        self.servertext = QLineEdit(self.serverbox)
        self.servertext.setPlaceholderText(_tr.m[3195, "Server"])
        self.servertext.setToolTip(_tr.m[3196, "Server"])
        self.servertext.editingFinished.connect(self._load_credentials)
        if self.host:
            self.servertext.setText(self.host if not self.port else
                                    "{}:{}".format(self.host, self.port))
        self.serverbox.layout().addWidget(self.servertext)

        self.databasetext = QLineEdit(self.serverbox)
        self.databasetext.setPlaceholderText(_tr.m[3197, "Database[/Schema]"])
        self.databasetext.setToolTip(_tr.m[3198, "Database or optionally Database/Schema"])
        if self.database:
            self.databasetext.setText(
                self.database if not self.schema else
                "{}/{}".format(self.database, self.schema))
        self.serverbox.layout().addWidget(self.databasetext)
        self.usernametext = QLineEdit(self.serverbox)
        self.usernametext.setPlaceholderText(_tr.m[3199, "Username"])
        self.usernametext.setToolTip(_tr.m[3200, "Username"])

        self.serverbox.layout().addWidget(self.usernametext)
        self.passwordtext = QLineEdit(self.serverbox)
        self.passwordtext.setPlaceholderText(_tr.m[3201, "Password"])
        self.passwordtext.setToolTip(_tr.m[3202, "Password"])
        self.passwordtext.setEchoMode(QLineEdit.Password)

        self.serverbox.layout().addWidget(self.passwordtext)

        self._load_credentials()

        self.connectbutton = gui.button(self.serverbox, self, _tr.m[3203, "Connect"],
                                        callback=self.connect)
        self.connectbutton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _load_credentials(self):
        self._parse_host_port()
        cm = self._credential_manager(self.host, self.port)
        self.username = cm.username
        self.password = cm.password

        if self.username:
            self.usernametext.setText(self.username)
        if self.password:
            self.passwordtext.setText(self.password)

    def _save_credentials(self):
        cm = self._credential_manager(self.host, self.port)
        cm.username = self.username or ""
        cm.password = self.password or ""

    @staticmethod
    def _credential_manager(host, port):
        return CredentialManager("SQL Table: {}:{}".format(host, port))

    def _parse_host_port(self):
        hostport = self.servertext.text().split(":")
        self.host = hostport[0]
        self.port = hostport[1] if len(hostport) == 2 else None

    def _check_db_settings(self):
        self._parse_host_port()
        self.database, _, self.schema = self.databasetext.text().partition("/")
        self.username = self.usernametext.text() or None
        self.password = self.passwordtext.text() or None

    def connect(self):
        self.clear()
        self._check_db_settings()
        if not self.host or not self.database:
            return
        try:
            backend = self.get_backend()
            if backend is None:
                return
            self.backend = backend(dict(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            ))
            self.on_connection_success()
        except BackendError as err:
            self.on_connection_error(err)

    def get_backend(self) -> Type[Backend]:
        """
        Derived widgets should override this to get corresponding backend.

        Returns
        -------
        backend: Type[Backend]
        """
        raise NotImplementedError

    def on_connection_success(self):
        self._save_credentials()
        self.database_desc = OrderedDict((
            (_tr.m[3204, "Host"], self.host), (_tr.m[3205, "Port"], self.port),
            (_tr.m[3206, "Database"], self.database), (_tr.m[3207, "User name"], self.username)
        ))

    def on_connection_error(self, err):
        error = str(err).split("\n")[0]
        self.Error.connection(error)

    def open_table(self):
        data = self.get_table()
        self.data_desc_table = data
        self.Outputs.data.send(data)

    def get_table(self) -> Table:
        """
        Derived widgets should override this to get corresponding table.

        Returns
        -------
        table: Table
        """
        raise NotImplementedError

    def clear(self):
        self.Error.connection.clear()
        self.database_desc = None
        self.data_desc_table = None
        self.Outputs.data.send(None)

    def send_report(self):
        if not self.database_desc:
            self.report_paragraph(_tr.m[3208, "No database connection."])
            return
        self.report_items(_tr.m[3209, "Database"], self.database_desc)
        if self.data_desc_table:
            self.report_items(_tr.m[3210, "Data"],
                              report.describe_data(self.data_desc_table))
