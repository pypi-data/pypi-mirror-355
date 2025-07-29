import os
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

import numpy as np

from AnyQt.QtWidgets import QFileDialog
from AnyQt.QtCore import Qt, QThread, pyqtSignal

from Orange.widgets import gui
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets.settings import Setting
from Orange.widgets.utils.concurrent import Task, ConcurrentMixin
from Orange.data import Table, Domain, StringVariable, ContinuousVariable

class TokenExtractorWorker(QThread):
    result = pyqtSignal(Table)  # emits the extract tokens Table
    progress = pyqtSignal(int)  # emits progress (0-100)

    def __init__(self, directory: str, top_n: int, normalize: bool):
        super().__init__()
        self.directory = directory
        self.top_n = top_n
        self.normalize = normalize

    def run(self):
        directory = self.directory
        top_n = self.top_n
        set_progress = self.progress.emit
        normalize = self.normalize

        counters = []
        titles = []
        all_tokens = Counter()
        files = [f for f in os.listdir(directory) if f.endswith(".xml") or f.endswith(".teixml")]

        for i, file in enumerate(files):
            path = os.path.join(directory, file)
            try:
                tree = ET.parse(path)
                root = tree.getroot()
                title = self._find_text(root, ["teiHeader", "fileDesc", "titleStmt", "title"])
                titles.append(title or os.path.splitext(file)[0])

                file_counter = Counter()
                for elem in root.iter():
                    if elem.tag.endswith("w"):
                        lemma = elem.attrib.get("lemma")
                        pos = elem.attrib.get("ana") or elem.attrib.get("pos")
                        if lemma and pos:
                            file_counter[(lemma, pos)] += 1

                counters.append(file_counter)
                all_tokens.update(file_counter)
            except Exception as e:
                print(f"Failed to process {file}: {e}")

            set_progress((100 * (i + 1)) // len(files))

        top_tokens = [tok for tok, _ in all_tokens.most_common(top_n)]
        variables = [ContinuousVariable("Total Tokens"), ContinuousVariable("Uniq Tokens")] + \
            [ContinuousVariable(f"{lemma}[{pos}]") for lemma, pos in top_tokens]
        domain = Domain(attributes=variables, class_vars=[], metas=[StringVariable("title")])

        rows = []
        for counter in counters:
            row = [counter.total(), len(counter)];
            if normalize:
                row.extend([ counter.get(t, 0)/counter.total() for t in top_tokens ])
            else:
                row.extend([ counter.get(t, 0) for t in top_tokens ])
            rows.append(row)

        rows = np.array(rows)
        new_Y = np.ndarray(shape=(len(rows), 0))
        metas = np.array([titles]).T

        self.result.emit(Table(domain, rows, new_Y, metas))

    def _find_text(self, root, tags):
        for tag in tags:
            found = next((el for el in root if el.tag.endswith(tag)), None)
            if found is None:
                return ""
            root = found
        return (root.text or "").strip()

class OWTEITokenExtractor(OWWidget, ConcurrentMixin):
    name = "TEI Token Extractor"
    description = "Extracts token frequencies from TEI-XML files."
    icon = "icons/tei.svg"
    priority = 10

    want_control_area = False

    class Outputs:
        data = Output("Data", Table)

    directory = Setting("")
    top_n = Setting(100)
    normalize = Setting(False)

    def __init__(self):
        super().__init__()

        self.worker = None
        self.table = None
        self.layout_main_area()
        if len(self.directory) > 0 and os.path.exists(self.directory):
            self.start_extraction()

    def layout_main_area(self):
        box = gui.vBox(self.mainArea, "TEI Token Extraction")

        self.dir_label = gui.label(box, self, "Selected Directory: None")
        gui.button(box, self, "Choose Directory", callback=self.choose_directory)
        self.top_spinner = gui.doubleSpin(box, self, "top_n", 10, 1000, step=1, label="Number of top tokens", decimals=0)
        self.normalize_checkbox = gui.checkBox(box, self, "normalize", "Normalize")
        self.normalize_checkbox.setToolTip("Divide the counts by the total number of tokens per document.")
        self.normalize_checkbox.clicked.connect(self.on_normalize_checked)
        self.extract_button = gui.button(box, self, "Extract Tokens", callback=self.start_extraction)
        self.mainArea.layout().setAlignment(Qt.AlignTop)

        self.progressBarInit()

    def choose_directory(self):
        dirpath = QFileDialog.getExistingDirectory(self, "Select TEI-XML Directory")
        if dirpath:
            self.directory = dirpath
            self.dir_label.setText(f"Selected Directory: {os.path.basename(dirpath)}")
    
    def on_normalize_checked(self):
        if self.table is not None:
            table = self.table
            X_df = table.X_df
            if self.normalize:
                X_df.iloc[:, 2:] = X_df.iloc[:, 2:].div(X_df.iloc[:, 1], axis=0)
            else:
                X_df.iloc[:, 2:] = X_df.iloc[:, 2:].multiply(X_df.iloc[:, 1], axis=0)

            new_table = Table(table.domain, X_df.to_numpy(), table.Y, table.metas)
            self.Outputs.data.send(new_table)

    def start_extraction(self):
        if not self.directory:
            self.error("Please choose a directory.")
            return
        self.error()
        self.progressBarInit()
        self.worker = TokenExtractorWorker(self.directory, int(self.top_n), self.normalize)
        self.worker.progress.connect(self.progressBarSet)
        self.worker.result.connect(self._on_result)
        self.worker.start()

    def _on_result(self, table: Table):
        self.progressBarFinished()
        self.table = table
        self.Outputs.data.send(table)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    w = WidgetPreview(OWTEITokenExtractor)
    w.create_widget()
    w.widget.directory = "/home/chris/Downloads/shakespeares-works_TEIsimple_FolgerShakespeare"
    w.run()
    