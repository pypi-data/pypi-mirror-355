from __future__ import annotations

import contextlib

from PyQt5.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


def commonpart_gen(w):
    layout = QGridLayout()
    label_comment = QLabel()
    label_comment.setText("Comment:")
    layout.addWidget(label_comment, 0, 0, 1, 2)
    w.edit_comment = QLineEdit()
    layout.addWidget(w.edit_comment, 1, 0, 2, 2)
    button_checked = QPushButton("Checked")
    button_checked.clicked.connect(w.checked)
    layout.addWidget(button_checked, 3, 1)

    button_back = QPushButton("Back")
    button_back.clicked.connect(w.back_page)
    button_next = QPushButton("Next")
    button_next.clicked.connect(w.next_page)
    layout.addWidget(button_back, 4, 0)
    layout.addWidget(button_next, 4, 1)

    return layout


def checklist_gen(w, page, tot_page):
    layout = QVBoxLayout()
    layout_child = QGridLayout()
    label_page = QLabel()
    label_page.setText(f"page: {page + 1}/{tot_page}")
    layout.addWidget(label_page)
    label = QLabel()
    label.setText("If there are any problems, check in checkbox.")
    layout.addWidget(label)

    w.cb = {}
    list_keys = list(w.parent.checklist_dict[str(page)].keys())
    for index_key, key in enumerate(list_keys):
        items = w.parent.checklist_dict[str(page)][key]
        w.cb[index_key] = {}
        for index, item in enumerate(items):
            w.cb[index_key][index] = QCheckBox(item, w)
            # w.cb[index].stateChanged.connect(lambda: w.checkBoxChangeAction(w.cb[index].checkState(),item))
            # print(type(item))
            layout_child.addWidget(w.cb[index_key][index], index, index_key)
            with contextlib.suppress(Exception):
                if item in w.parent.anomaly_dic[str(page)]:
                    w.cb[index_key][index].toggle()
    layout.addLayout(layout_child)
    layout.addLayout(commonpart_gen(w))

    return layout
