from __future__ import annotations

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

    if page == 0:
        w.cb_SMD_0_0 = QCheckBox("SMD_0_0", w)
        w.cb_SMD_0_1 = QCheckBox("SMD_0_1", w)
        w.cb_SMD_0_2 = QCheckBox("SMD_0_2", w)
        w.cb_SMD_0_3 = QCheckBox("SMD_0_3", w)
        w.cb_SMD_0_4 = QCheckBox("SMD_0_4", w)
        w.cb_SMD_0_5 = QCheckBox("SMD_0_5", w)
        w.cb_SMD_0_6 = QCheckBox("SMD_0_6", w)
        w.cb_Plating_0_0 = QCheckBox("Plating_0_0", w)
        w.cb_Plating_0_1 = QCheckBox("Plating_0_1", w)
        w.cb_Plating_0_2 = QCheckBox("Plating_0_2", w)
        w.cb_Plating_0_3 = QCheckBox("Plating_0_3", w)
        w.cb_Plating_0_4 = QCheckBox("Plating_0_4", w)
        w.cb_Plating_0_5 = QCheckBox("Plating_0_5", w)
        w.cb_Plating_0_6 = QCheckBox("Plating_0_6", w)
        w.cb_Plating_0_7 = QCheckBox("Plating_0_7", w)
        w.cb_Plating_0_8 = QCheckBox("Plating_0_8", w)
        w.cb_Plating_0_9 = QCheckBox("Plating_0_9", w)
        w.cb_Plating_0_10 = QCheckBox("Plating_0_10", w)
        w.cb_Plating_0_11 = QCheckBox("Plating_0_11", w)

        w.cb_SMD_0_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_0_0.checkState(), "SMD_0_0")
        )
        w.cb_SMD_0_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_0_1.checkState(), "SMD_0_1")
        )
        w.cb_SMD_0_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_0_2.checkState(), "SMD_0_2")
        )
        w.cb_SMD_0_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_0_3.checkState(), "SMD_0_3")
        )
        w.cb_SMD_0_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_0_4.checkState(), "SMD_0_4")
        )
        w.cb_SMD_0_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_0_5.checkState(), "SMD_0_5")
        )
        w.cb_SMD_0_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_0_6.checkState(), "SMD_0_6")
        )
        w.cb_Plating_0_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_0.checkState(), "Plating_0_0")
        )
        w.cb_Plating_0_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_1.checkState(), "Plating_0_1")
        )
        w.cb_Plating_0_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_2.checkState(), "Plating_0_2")
        )
        w.cb_Plating_0_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_3.checkState(), "Plating_0_3")
        )
        w.cb_Plating_0_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_4.checkState(), "Plating_0_4")
        )
        w.cb_Plating_0_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_5.checkState(), "Plating_0_5")
        )
        w.cb_Plating_0_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_6.checkState(), "Plating_0_6")
        )
        w.cb_Plating_0_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_7.checkState(), "Plating_0_7")
        )
        w.cb_Plating_0_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_8.checkState(), "Plating_0_8")
        )
        w.cb_Plating_0_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_0_9.checkState(), "Plating_0_9")
        )
        w.cb_Plating_0_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_0_10.checkState(), "Plating_0_10"
            )
        )
        w.cb_Plating_0_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_0_11.checkState(), "Plating_0_11"
            )
        )

        layout_child.addWidget(w.cb_SMD_0_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_0_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_0_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_0_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_0_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_0_5, 5, 1)
        layout_child.addWidget(w.cb_SMD_0_6, 6, 1)
        layout_child.addWidget(w.cb_Plating_0_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_0_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_0_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_0_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_0_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_0_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_0_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_0_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_0_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_0_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_0_10, 10, 0)
        layout_child.addWidget(w.cb_Plating_0_11, 11, 0)

        w.status_update(page)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 1:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 2:
        w.cb_Plating_2_0 = QCheckBox("Plating_2_0", w)

        w.cb_Plating_2_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_2_0.checkState(), "Plating_2_0")
        )

        layout_child.addWidget(w.cb_Plating_2_0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 3:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 4:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 5:
        w.cb_SMD_5_0 = QCheckBox("SMD_5_0", w)
        w.cb_SMD_5_1 = QCheckBox("SMD_5_1", w)
        w.cb_SMD_5_2 = QCheckBox("SMD_5_2", w)
        w.cb_SMD_5_3 = QCheckBox("SMD_5_3", w)
        w.cb_SMD_5_4 = QCheckBox("SMD_5_4", w)
        w.cb_Plating_5_0 = QCheckBox("Plating_5_0", w)
        w.cb_Plating_5_1 = QCheckBox("Plating_5_1", w)
        w.cb_Plating_5_2 = QCheckBox("Plating_5_2", w)
        w.cb_Plating_5_3 = QCheckBox("Plating_5_3", w)
        w.cb_Plating_5_4 = QCheckBox("Plating_5_4", w)
        w.cb_Plating_5_5 = QCheckBox("Plating_5_5", w)
        w.cb_Plating_5_6 = QCheckBox("Plating_5_6", w)
        w.cb_Plating_5_7 = QCheckBox("Plating_5_7", w)

        w.cb_SMD_5_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_5_0.checkState(), "SMD_5_0")
        )
        w.cb_SMD_5_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_5_0.checkState(), "SMD_5_1")
        )
        w.cb_SMD_5_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_5_0.checkState(), "SMD_5_2")
        )
        w.cb_SMD_5_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_5_0.checkState(), "SMD_5_3")
        )
        w.cb_SMD_5_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_5_0.checkState(), "SMD_5_4")
        )
        w.cb_Plating_5_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_5_0.checkState(), "Plating_5_0")
        )
        w.cb_Plating_5_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_5_1.checkState(), "Plating_5_1")
        )
        w.cb_Plating_5_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_5_2.checkState(), "Plating_5_2")
        )
        w.cb_Plating_5_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_5_3.checkState(), "Plating_5_3")
        )
        w.cb_Plating_5_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_5_4.checkState(), "Plating_5_4")
        )
        w.cb_Plating_5_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_5_5.checkState(), "Plating_5_5")
        )
        w.cb_Plating_5_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_5_6.checkState(), "Plating_5_6")
        )
        w.cb_Plating_5_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_5_7.checkState(), "Plating_5_7")
        )

        layout_child.addWidget(w.cb_SMD_5_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_5_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_5_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_5_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_5_4, 4, 1)
        layout_child.addWidget(w.cb_Plating_5_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_5_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_5_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_5_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_5_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_5_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_5_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_5_7, 7, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 6:
        w.cb_SMD_6_0 = QCheckBox("SMD_6_0", w)
        w.cb_SMD_6_1 = QCheckBox("SMD_6_1", w)
        w.cb_SMD_6_2 = QCheckBox("SMD_6_2", w)
        w.cb_SMD_6_3 = QCheckBox("SMD_6_3", w)
        w.cb_SMD_6_4 = QCheckBox("SMD_6_4", w)
        w.cb_SMD_6_5 = QCheckBox("SMD_6_5", w)
        w.cb_Plating_6_0 = QCheckBox("Plating_6_0", w)
        w.cb_Plating_6_1 = QCheckBox("Plating_6_1", w)
        w.cb_Plating_6_2 = QCheckBox("Plating_6_2", w)
        w.cb_Plating_6_3 = QCheckBox("Plating_6_3", w)
        w.cb_Plating_6_4 = QCheckBox("Plating_6_4", w)
        w.cb_Plating_6_5 = QCheckBox("Plating_6_5", w)
        w.cb_Plating_6_6 = QCheckBox("Plating_6_6", w)
        w.cb_Plating_6_7 = QCheckBox("Plating_6_7", w)
        w.cb_Plating_6_8 = QCheckBox("Plating_6_8", w)
        w.cb_Plating_6_9 = QCheckBox("Plating_6_9", w)
        w.cb_Plating_6_10 = QCheckBox("Plating_6_10", w)
        w.cb_Plating_6_11 = QCheckBox("Plating_6_11", w)
        w.cb_Plating_6_12 = QCheckBox("Plating_6_12", w)
        w.cb_Plating_6_13 = QCheckBox("Plating_6_13", w)
        w.cb_Plating_6_14 = QCheckBox("Plating_6_14", w)
        w.cb_Plating_6_15 = QCheckBox("Plating_6_15", w)
        w.cb_Plating_6_16 = QCheckBox("Plating_6_16", w)
        w.cb_Plating_6_17 = QCheckBox("Plating_6_17", w)
        w.cb_Plating_6_18 = QCheckBox("Plating_6_18", w)

        w.cb_SMD_6_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_6_0.checkState(), "SMD_6_0")
        )
        w.cb_SMD_6_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_6_1.checkState(), "SMD_6_1")
        )
        w.cb_SMD_6_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_6_2.checkState(), "SMD_6_2")
        )
        w.cb_SMD_6_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_6_3.checkState(), "SMD_6_3")
        )
        w.cb_SMD_6_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_6_4.checkState(), "SMD_6_4")
        )
        w.cb_SMD_6_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_6_5.checkState(), "SMD_6_5")
        )
        w.cb_Plating_6_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_0.checkState(), "Plating_6_0")
        )
        w.cb_Plating_6_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_1.checkState(), "Plating_6_1")
        )
        w.cb_Plating_6_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_2.checkState(), "Plating_6_2")
        )
        w.cb_Plating_6_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_3.checkState(), "Plating_6_3")
        )
        w.cb_Plating_6_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_4.checkState(), "Plating_6_4")
        )
        w.cb_Plating_6_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_5.checkState(), "Plating_6_5")
        )
        w.cb_Plating_6_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_6.checkState(), "Plating_6_6")
        )
        w.cb_Plating_6_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_7.checkState(), "Plating_6_7")
        )
        w.cb_Plating_6_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_8.checkState(), "Plating_6_8")
        )
        w.cb_Plating_6_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Plating_6_9.checkState(), "Plating_6_9")
        )
        w.cb_Plating_6_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_10.checkState(), "Plating_6_10"
            )
        )
        w.cb_Plating_6_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_11.checkState(), "Plating_6_11"
            )
        )
        w.cb_Plating_6_12.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_12.checkState(), "Plating_6_12"
            )
        )
        w.cb_Plating_6_13.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_13.checkState(), "Plating_6_13"
            )
        )
        w.cb_Plating_6_14.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_14.checkState(), "Plating_6_14"
            )
        )
        w.cb_Plating_6_15.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_15.checkState(), "Plating_6_15"
            )
        )
        w.cb_Plating_6_16.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_16.checkState(), "Plating_6_16"
            )
        )
        w.cb_Plating_6_17.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_17.checkState(), "Plating_6_17"
            )
        )
        w.cb_Plating_6_18.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_6_18.checkState(), "Plating_6_18"
            )
        )

        layout_child.addWidget(w.cb_SMD_6_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_6_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_6_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_6_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_6_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_6_5, 5, 1)
        layout_child.addWidget(w.cb_Plating_6_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_6_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_6_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_6_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_6_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_6_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_6_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_6_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_6_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_6_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_6_10, 10, 0)
        layout_child.addWidget(w.cb_Plating_6_11, 11, 0)
        layout_child.addWidget(w.cb_Plating_6_12, 12, 0)
        layout_child.addWidget(w.cb_Plating_6_13, 13, 0)
        layout_child.addWidget(w.cb_Plating_6_14, 14, 0)
        layout_child.addWidget(w.cb_Plating_6_15, 15, 0)
        layout_child.addWidget(w.cb_Plating_6_16, 16, 0)
        layout_child.addWidget(w.cb_Plating_6_17, 17, 0)
        layout_child.addWidget(w.cb_Plating_6_18, 18, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 7:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 8:
        w.cb_SMD_8_0 = QCheckBox("SMD_8_0", w)
        w.cb_SMD_8_1 = QCheckBox("SMD_8_1", w)

        w.cb_SMD_8_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_8_0.checkState(), "SMD_8_0")
        )
        w.cb_SMD_8_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_8_1.checkState(), "SMD_8_1")
        )

        layout_child.addWidget(w.cb_SMD_8_0)
        layout_child.addWidget(w.cb_SMD_8_1)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 9:
        w.cb_SMD_9_0 = QCheckBox("SMD_9_0", w)
        w.cb_SMD_9_1 = QCheckBox("SMD_9_1", w)

        w.cb_SMD_9_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_9_0.checkState(), "SMD_9_0")
        )
        w.cb_SMD_9_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_9_1.checkState(), "SMD_9_1")
        )

        layout_child.addWidget(w.cb_SMD_9_0)
        layout_child.addWidget(w.cb_SMD_9_1)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 10:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 11:
        w.cb_SMD_11_0 = QCheckBox("SMD_11_0", w)
        w.cb_SMD_11_1 = QCheckBox("SMD_11_1", w)
        w.cb_SMD_11_2 = QCheckBox("SMD_11_2", w)
        w.cb_SMD_11_3 = QCheckBox("SMD_11_3", w)
        w.cb_SMD_11_4 = QCheckBox("SMD_11_4", w)
        w.cb_SMD_11_5 = QCheckBox("SMD_11_5", w)
        w.cb_Plating_11_0 = QCheckBox("Plating_11_0", w)
        w.cb_Plating_11_1 = QCheckBox("Plating_11_1", w)
        w.cb_Plating_11_2 = QCheckBox("Plating_11_2", w)
        w.cb_Plating_11_3 = QCheckBox("Plating_11_3", w)
        w.cb_Plating_11_4 = QCheckBox("Plating_11_4", w)
        w.cb_Plating_11_5 = QCheckBox("Plating_11_5", w)
        w.cb_Plating_11_6 = QCheckBox("Plating_11_6", w)
        w.cb_Plating_11_7 = QCheckBox("Plating_11_7", w)
        w.cb_Plating_11_8 = QCheckBox("Plating_11_8", w)
        w.cb_Plating_11_9 = QCheckBox("Plating_11_9", w)
        w.cb_Plating_11_10 = QCheckBox("Plating_11_10", w)
        w.cb_Plating_11_11 = QCheckBox("Plating_11_11", w)
        w.cb_Plating_11_12 = QCheckBox("Plating_11_12", w)
        w.cb_Plating_11_13 = QCheckBox("Plating_11_13", w)
        w.cb_Plating_11_14 = QCheckBox("Plating_11_14", w)
        w.cb_Plating_11_15 = QCheckBox("Plating_11_15", w)
        w.cb_Plating_11_16 = QCheckBox("Plating_11_16", w)
        w.cb_Plating_11_17 = QCheckBox("Plating_11_17", w)

        w.cb_SMD_11_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_11_0.checkState(), "SMD_11_0")
        )
        w.cb_SMD_11_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_11_1.checkState(), "SMD_11_1")
        )
        w.cb_SMD_11_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_11_2.checkState(), "SMD_11_2")
        )
        w.cb_SMD_11_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_11_3.checkState(), "SMD_11_3")
        )
        w.cb_SMD_11_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_11_4.checkState(), "SMD_11_4")
        )
        w.cb_SMD_11_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_11_5.checkState(), "SMD_11_5")
        )
        w.cb_Plating_11_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_0.checkState(), "Plating_11_0"
            )
        )
        w.cb_Plating_11_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_1.checkState(), "Plating_11_1"
            )
        )
        w.cb_Plating_11_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_2.checkState(), "Plating_11_2"
            )
        )
        w.cb_Plating_11_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_3.checkState(), "Plating_11_3"
            )
        )
        w.cb_Plating_11_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_4.checkState(), "Plating_11_4"
            )
        )
        w.cb_Plating_11_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_5.checkState(), "Plating_11_5"
            )
        )
        w.cb_Plating_11_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_6.checkState(), "Plating_11_6"
            )
        )
        w.cb_Plating_11_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_7.checkState(), "Plating_11_7"
            )
        )
        w.cb_Plating_11_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_8.checkState(), "Plating_11_8"
            )
        )
        w.cb_Plating_11_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_9.checkState(), "Plating_11_9"
            )
        )
        w.cb_Plating_11_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_10.checkState(), "Plating_11_10"
            )
        )
        w.cb_Plating_11_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_11.checkState(), "Plating_11_11"
            )
        )
        w.cb_Plating_11_12.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_12.checkState(), "Plating_11_12"
            )
        )
        w.cb_Plating_11_13.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_13.checkState(), "Plating_11_13"
            )
        )
        w.cb_Plating_11_14.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_14.checkState(), "Plating_11_14"
            )
        )
        w.cb_Plating_11_15.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_15.checkState(), "Plating_11_15"
            )
        )
        w.cb_Plating_11_16.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_16.checkState(), "Plating_11_16"
            )
        )
        w.cb_Plating_11_17.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_11_17.checkState(), "Plating_11_17"
            )
        )

        layout_child.addWidget(w.cb_SMD_11_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_11_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_11_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_11_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_11_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_11_5, 5, 1)
        layout_child.addWidget(w.cb_Plating_11_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_11_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_11_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_11_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_11_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_11_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_11_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_11_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_11_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_11_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_11_10, 10, 0)
        layout_child.addWidget(w.cb_Plating_11_11, 11, 0)
        layout_child.addWidget(w.cb_Plating_11_12, 12, 0)
        layout_child.addWidget(w.cb_Plating_11_13, 13, 0)
        layout_child.addWidget(w.cb_Plating_11_14, 14, 0)
        layout_child.addWidget(w.cb_Plating_11_15, 15, 0)
        layout_child.addWidget(w.cb_Plating_11_16, 16, 0)
        layout_child.addWidget(w.cb_Plating_11_17, 17, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 12:
        w.cb_SMD_12_0 = QCheckBox("SMD_12_0", w)
        w.cb_SMD_12_1 = QCheckBox("SMD_12_1", w)
        w.cb_SMD_12_2 = QCheckBox("SMD_12_2", w)
        w.cb_SMD_12_3 = QCheckBox("SMD_12_3", w)
        w.cb_SMD_12_4 = QCheckBox("SMD_12_4", w)
        w.cb_SMD_12_5 = QCheckBox("SMD_12_5", w)
        w.cb_SMD_12_6 = QCheckBox("SMD_12_6", w)
        w.cb_Plating_12_0 = QCheckBox("Plating_12_0", w)
        w.cb_Plating_12_1 = QCheckBox("Plating_12_1", w)
        w.cb_Plating_12_2 = QCheckBox("Plating_12_2", w)
        w.cb_Plating_12_3 = QCheckBox("Plating_12_3", w)
        w.cb_Plating_12_4 = QCheckBox("Plating_12_4", w)
        w.cb_Plating_12_5 = QCheckBox("Plating_12_5", w)
        w.cb_Plating_12_6 = QCheckBox("Plating_12_6", w)
        w.cb_Plating_12_7 = QCheckBox("Plating_12_7", w)
        w.cb_Plating_12_8 = QCheckBox("Plating_12_8", w)
        w.cb_Plating_12_9 = QCheckBox("Plating_12_9", w)
        w.cb_Plating_12_10 = QCheckBox("Plating_12_10", w)

        w.cb_SMD_12_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_12_0.checkState(), "SMD_12_0")
        )
        w.cb_SMD_12_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_12_1.checkState(), "SMD_12_1")
        )
        w.cb_SMD_12_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_12_2.checkState(), "SMD_12_2")
        )
        w.cb_SMD_12_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_12_3.checkState(), "SMD_12_3")
        )
        w.cb_SMD_12_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_12_4.checkState(), "SMD_12_4")
        )
        w.cb_SMD_12_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_12_5.checkState(), "SMD_12_5")
        )
        w.cb_SMD_12_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_12_6.checkState(), "SMD_12_6")
        )
        w.cb_Plating_12_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_0.checkState(), "Plating_12_0"
            )
        )
        w.cb_Plating_12_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_1.checkState(), "Plating_12_1"
            )
        )
        w.cb_Plating_12_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_2.checkState(), "Plating_12_2"
            )
        )
        w.cb_Plating_12_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_3.checkState(), "Plating_12_3"
            )
        )
        w.cb_Plating_12_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_4.checkState(), "Plating_12_4"
            )
        )
        w.cb_Plating_12_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_5.checkState(), "Plating_12_5"
            )
        )
        w.cb_Plating_12_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_6.checkState(), "Plating_12_6"
            )
        )
        w.cb_Plating_12_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_7.checkState(), "Plating_12_7"
            )
        )
        w.cb_Plating_12_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_8.checkState(), "Plating_12_8"
            )
        )
        w.cb_Plating_12_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_9.checkState(), "Plating_12_9"
            )
        )
        w.cb_Plating_12_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_12_10.checkState(), "Plating_12_10"
            )
        )

        layout_child.addWidget(w.cb_SMD_12_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_12_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_12_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_12_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_12_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_12_5, 5, 1)
        layout_child.addWidget(w.cb_SMD_12_6, 6, 1)
        layout_child.addWidget(w.cb_Plating_12_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_12_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_12_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_12_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_12_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_12_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_12_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_12_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_12_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_12_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_12_10, 10, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 13:
        w.cb_SMD_13_0 = QCheckBox("SMD_13_0", w)

        w.cb_SMD_13_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_13_0.checkState(), "SMD_13_0")
        )

        layout_child.addWidget(w.cb_SMD_13_0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 14:
        w.cb_SMD_14_0 = QCheckBox("SMD_14_0", w)
        w.cb_SMD_14_1 = QCheckBox("SMD_14_1", w)
        w.cb_SMD_14_2 = QCheckBox("SMD_14_2", w)
        w.cb_SMD_14_3 = QCheckBox("SMD_14_3", w)
        w.cb_SMD_14_4 = QCheckBox("SMD_14_4", w)
        w.cb_SMD_14_5 = QCheckBox("SMD_14_5", w)
        w.cb_SMD_14_6 = QCheckBox("SMD_14_6", w)

        w.cb_SMD_14_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_14_0.checkState(), "SMD_14_0")
        )
        w.cb_SMD_14_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_14_1.checkState(), "SMD_14_1")
        )
        w.cb_SMD_14_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_14_2.checkState(), "SMD_14_2")
        )
        w.cb_SMD_14_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_14_3.checkState(), "SMD_14_3")
        )
        w.cb_SMD_14_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_14_4.checkState(), "SMD_14_4")
        )
        w.cb_SMD_14_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_14_5.checkState(), "SMD_14_5")
        )
        w.cb_SMD_14_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_14_6.checkState(), "SMD_14_6")
        )

        layout_child.addWidget(w.cb_SMD_14_0)
        layout_child.addWidget(w.cb_SMD_14_1)
        layout_child.addWidget(w.cb_SMD_14_2)
        layout_child.addWidget(w.cb_SMD_14_3)
        layout_child.addWidget(w.cb_SMD_14_4)
        layout_child.addWidget(w.cb_SMD_14_5)
        layout_child.addWidget(w.cb_SMD_14_6)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 15:
        w.cb_SMD_15_0 = QCheckBox("SMD_15_0", w)
        w.cb_SMD_15_1 = QCheckBox("SMD_15_1", w)
        w.cb_SMD_15_2 = QCheckBox("SMD_15_2", w)
        w.cb_SMD_15_3 = QCheckBox("SMD_15_3", w)
        w.cb_SMD_15_4 = QCheckBox("SMD_15_4", w)
        w.cb_SMD_15_5 = QCheckBox("SMD_15_5", w)
        w.cb_SMD_15_6 = QCheckBox("SMD_15_6", w)
        w.cb_SMD_15_7 = QCheckBox("SMD_15_7", w)

        w.cb_SMD_15_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_15_0.checkState(), "SMD_15_0")
        )
        w.cb_SMD_15_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_15_1.checkState(), "SMD_15_1")
        )
        w.cb_SMD_15_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_15_2.checkState(), "SMD_15_2")
        )
        w.cb_SMD_15_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_15_3.checkState(), "SMD_15_3")
        )
        w.cb_SMD_15_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_15_4.checkState(), "SMD_15_4")
        )
        w.cb_SMD_15_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_15_5.checkState(), "SMD_15_5")
        )
        w.cb_SMD_15_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_15_6.checkState(), "SMD_15_6")
        )
        w.cb_SMD_15_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_15_7.checkState(), "SMD_15_7")
        )

        layout_child.addWidget(w.cb_SMD_15_0)
        layout_child.addWidget(w.cb_SMD_15_1)
        layout_child.addWidget(w.cb_SMD_15_2)
        layout_child.addWidget(w.cb_SMD_15_3)
        layout_child.addWidget(w.cb_SMD_15_4)
        layout_child.addWidget(w.cb_SMD_15_5)
        layout_child.addWidget(w.cb_SMD_15_6)
        layout_child.addWidget(w.cb_SMD_15_7)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 16:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 17:
        w.cb_SMD_17_0 = QCheckBox("SMD_17_0", w)
        w.cb_SMD_17_1 = QCheckBox("SMD_17_1", w)
        w.cb_SMD_17_2 = QCheckBox("SMD_17_2", w)
        w.cb_SMD_17_3 = QCheckBox("SMD_17_3", w)
        w.cb_SMD_17_4 = QCheckBox("SMD_17_4", w)
        w.cb_SMD_17_5 = QCheckBox("SMD_17_5", w)
        w.cb_SMD_17_6 = QCheckBox("SMD_17_6", w)
        w.cb_SMD_17_7 = QCheckBox("SMD_17_7", w)
        w.cb_SMD_17_8 = QCheckBox("SMD_17_8", w)
        w.cb_Plating_17_0 = QCheckBox("Plating_17_0", w)
        w.cb_Plating_17_1 = QCheckBox("Plating_17_1", w)
        w.cb_Plating_17_2 = QCheckBox("Plating_17_2", w)
        w.cb_Plating_17_3 = QCheckBox("Plating_17_3", w)
        w.cb_Plating_17_4 = QCheckBox("Plating_17_4", w)
        w.cb_Plating_17_5 = QCheckBox("Plating_17_5", w)
        w.cb_Plating_17_6 = QCheckBox("Plating_17_6", w)
        w.cb_Plating_17_7 = QCheckBox("Plating_17_7", w)
        w.cb_Plating_17_8 = QCheckBox("Plating_17_8", w)
        w.cb_Plating_17_9 = QCheckBox("Plating_17_9", w)
        w.cb_Plating_17_10 = QCheckBox("Plating_17_10", w)
        w.cb_Plating_17_11 = QCheckBox("Plating_17_11", w)
        w.cb_Plating_17_12 = QCheckBox("Plating_17_12", w)
        w.cb_Plating_17_13 = QCheckBox("Plating_17_13", w)
        w.cb_Plating_17_14 = QCheckBox("Plating_17_14", w)

        w.cb_SMD_17_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_0.checkState(), "SMD_17_0")
        )
        w.cb_SMD_17_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_1.checkState(), "SMD_17_1")
        )
        w.cb_SMD_17_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_2.checkState(), "SMD_17_2")
        )
        w.cb_SMD_17_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_3.checkState(), "SMD_17_3")
        )
        w.cb_SMD_17_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_4.checkState(), "SMD_17_4")
        )
        w.cb_SMD_17_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_5.checkState(), "SMD_17_5")
        )
        w.cb_SMD_17_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_6.checkState(), "SMD_17_6")
        )
        w.cb_SMD_17_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_7.checkState(), "SMD_17_7")
        )
        w.cb_SMD_17_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_17_8.checkState(), "SMD_17_8")
        )
        w.cb_Plating_17_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_0.checkState(), "Plating_17_0"
            )
        )
        w.cb_Plating_17_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_1.checkState(), "Plating_17_1"
            )
        )
        w.cb_Plating_17_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_2.checkState(), "Plating_17_2"
            )
        )
        w.cb_Plating_17_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_3.checkState(), "Plating_17_3"
            )
        )
        w.cb_Plating_17_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_4.checkState(), "Plating_17_4"
            )
        )
        w.cb_Plating_17_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_5.checkState(), "Plating_17_5"
            )
        )
        w.cb_Plating_17_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_6.checkState(), "Plating_17_6"
            )
        )
        w.cb_Plating_17_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_7.checkState(), "Plating_17_7"
            )
        )
        w.cb_Plating_17_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_8.checkState(), "Plating_17_8"
            )
        )
        w.cb_Plating_17_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_9.checkState(), "Plating_17_9"
            )
        )
        w.cb_Plating_17_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_10.checkState(), "Plating_17_10"
            )
        )
        w.cb_Plating_17_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_11.checkState(), "Plating_17_11"
            )
        )
        w.cb_Plating_17_12.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_12.checkState(), "Plating_17_12"
            )
        )
        w.cb_Plating_17_13.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_13.checkState(), "Plating_17_13"
            )
        )
        w.cb_Plating_17_14.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_17_14.checkState(), "Plating_17_14"
            )
        )

        layout_child.addWidget(w.cb_SMD_17_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_17_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_17_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_17_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_17_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_17_5, 5, 1)
        layout_child.addWidget(w.cb_SMD_17_6, 6, 1)
        layout_child.addWidget(w.cb_SMD_17_7, 7, 1)
        layout_child.addWidget(w.cb_SMD_17_8, 8, 1)
        layout_child.addWidget(w.cb_Plating_17_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_17_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_17_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_17_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_17_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_17_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_17_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_17_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_17_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_17_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_17_10, 10, 0)
        layout_child.addWidget(w.cb_Plating_17_11, 11, 0)
        layout_child.addWidget(w.cb_Plating_17_12, 12, 0)
        layout_child.addWidget(w.cb_Plating_17_13, 13, 0)
        layout_child.addWidget(w.cb_Plating_17_14, 14, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 18:
        w.cb_SMD_18_0 = QCheckBox("SMD_18_0", w)
        w.cb_SMD_18_1 = QCheckBox("SMD_18_1", w)
        w.cb_SMD_18_2 = QCheckBox("SMD_18_2", w)
        w.cb_SMD_18_3 = QCheckBox("SMD_18_3", w)
        w.cb_SMD_18_4 = QCheckBox("SMD_18_4", w)
        w.cb_SMD_18_5 = QCheckBox("SMD_18_5", w)
        w.cb_SMD_18_6 = QCheckBox("SMD_18_6", w)
        w.cb_SMD_18_7 = QCheckBox("SMD_18_7", w)
        w.cb_SMD_18_8 = QCheckBox("SMD_18_8", w)
        w.cb_Plating_18_0 = QCheckBox("Plating_18_0", w)
        w.cb_Plating_18_1 = QCheckBox("Plating_18_1", w)
        w.cb_Plating_18_2 = QCheckBox("Plating_18_2", w)
        w.cb_Plating_18_3 = QCheckBox("Plating_18_3", w)
        w.cb_Plating_18_4 = QCheckBox("Plating_18_4", w)
        w.cb_Plating_18_5 = QCheckBox("Plating_18_5", w)
        w.cb_Plating_18_6 = QCheckBox("Plating_18_6", w)
        w.cb_Plating_18_7 = QCheckBox("Plating_18_7", w)
        w.cb_Plating_18_8 = QCheckBox("Plating_18_8", w)
        w.cb_Plating_18_9 = QCheckBox("Plating_18_9", w)
        w.cb_Plating_18_10 = QCheckBox("Plating_18_10", w)
        w.cb_Plating_18_11 = QCheckBox("Plating_18_11", w)
        w.cb_Plating_18_12 = QCheckBox("Plating_18_12", w)
        w.cb_Plating_18_13 = QCheckBox("Plating_18_13", w)
        w.cb_Plating_18_14 = QCheckBox("Plating_18_14", w)

        w.cb_SMD_18_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_0.checkState(), "SMD_18_0")
        )
        w.cb_SMD_18_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_1.checkState(), "SMD_18_1")
        )
        w.cb_SMD_18_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_2.checkState(), "SMD_18_2")
        )
        w.cb_SMD_18_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_3.checkState(), "SMD_18_3")
        )
        w.cb_SMD_18_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_4.checkState(), "SMD_18_4")
        )
        w.cb_SMD_18_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_5.checkState(), "SMD_18_5")
        )
        w.cb_SMD_18_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_6.checkState(), "SMD_18_6")
        )
        w.cb_SMD_18_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_7.checkState(), "SMD_18_7")
        )
        w.cb_SMD_18_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_18_8.checkState(), "SMD_18_8")
        )
        w.cb_Plating_18_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_0.checkState(), "Plating_18_0"
            )
        )
        w.cb_Plating_18_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_1.checkState(), "Plating_18_1"
            )
        )
        w.cb_Plating_18_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_2.checkState(), "Plating_18_2"
            )
        )
        w.cb_Plating_18_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_3.checkState(), "Plating_18_3"
            )
        )
        w.cb_Plating_18_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_4.checkState(), "Plating_18_4"
            )
        )
        w.cb_Plating_18_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_5.checkState(), "Plating_18_5"
            )
        )
        w.cb_Plating_18_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_6.checkState(), "Plating_18_6"
            )
        )
        w.cb_Plating_18_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_7.checkState(), "Plating_18_7"
            )
        )
        w.cb_Plating_18_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_8.checkState(), "Plating_18_8"
            )
        )
        w.cb_Plating_18_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_9.checkState(), "Plating_18_9"
            )
        )
        w.cb_Plating_18_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_10.checkState(), "Plating_18_10"
            )
        )
        w.cb_Plating_18_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_11.checkState(), "Plating_18_11"
            )
        )
        w.cb_Plating_18_12.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_12.checkState(), "Plating_18_12"
            )
        )
        w.cb_Plating_18_13.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_13.checkState(), "Plating_18_13"
            )
        )
        w.cb_Plating_18_14.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_18_14.checkState(), "Plating_18_14"
            )
        )

        layout_child.addWidget(w.cb_SMD_18_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_18_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_18_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_18_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_18_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_18_5, 5, 1)
        layout_child.addWidget(w.cb_SMD_18_6, 6, 1)
        layout_child.addWidget(w.cb_SMD_18_7, 7, 1)
        layout_child.addWidget(w.cb_SMD_18_8, 8, 1)
        layout_child.addWidget(w.cb_Plating_18_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_18_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_18_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_18_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_18_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_18_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_18_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_18_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_18_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_18_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_18_10, 10, 0)
        layout_child.addWidget(w.cb_Plating_18_11, 11, 0)
        layout_child.addWidget(w.cb_Plating_18_12, 12, 0)
        layout_child.addWidget(w.cb_Plating_18_13, 13, 0)
        layout_child.addWidget(w.cb_Plating_18_14, 14, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 19:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 20:
        w.cb_SMD_20_0 = QCheckBox("SMD_20_0", w)
        w.cb_SMD_20_1 = QCheckBox("SMD_20_1", w)
        w.cb_SMD_20_2 = QCheckBox("SMD_20_2", w)
        w.cb_SMD_20_3 = QCheckBox("SMD_20_3", w)
        w.cb_SMD_20_4 = QCheckBox("SMD_20_4", w)
        w.cb_SMD_20_5 = QCheckBox("SMD_20_5", w)
        w.cb_SMD_20_6 = QCheckBox("SMD_20_6", w)
        w.cb_SMD_20_7 = QCheckBox("SMD_20_7", w)
        w.cb_SMD_20_8 = QCheckBox("SMD_20_8", w)

        w.cb_SMD_20_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_0.checkState(), "SMD_20_0")
        )
        w.cb_SMD_20_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_1.checkState(), "SMD_20_1")
        )
        w.cb_SMD_20_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_2.checkState(), "SMD_20_2")
        )
        w.cb_SMD_20_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_3.checkState(), "SMD_20_3")
        )
        w.cb_SMD_20_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_4.checkState(), "SMD_20_4")
        )
        w.cb_SMD_20_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_5.checkState(), "SMD_20_5")
        )
        w.cb_SMD_20_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_6.checkState(), "SMD_20_6")
        )
        w.cb_SMD_20_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_7.checkState(), "SMD_20_7")
        )
        w.cb_SMD_20_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_20_8.checkState(), "SMD_20_8")
        )

        layout_child.addWidget(w.cb_SMD_20_0)
        layout_child.addWidget(w.cb_SMD_20_1)
        layout_child.addWidget(w.cb_SMD_20_2)
        layout_child.addWidget(w.cb_SMD_20_3)
        layout_child.addWidget(w.cb_SMD_20_4)
        layout_child.addWidget(w.cb_SMD_20_5)
        layout_child.addWidget(w.cb_SMD_20_6)
        layout_child.addWidget(w.cb_SMD_20_7)
        layout_child.addWidget(w.cb_SMD_20_8)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 21:
        w.cb_SMD_21_0 = QCheckBox("SMD_21_0", w)
        w.cb_SMD_21_1 = QCheckBox("SMD_21_1", w)
        w.cb_SMD_21_2 = QCheckBox("SMD_21_2", w)
        w.cb_SMD_21_3 = QCheckBox("SMD_21_3", w)
        w.cb_SMD_21_4 = QCheckBox("SMD_21_4", w)
        w.cb_SMD_21_5 = QCheckBox("SMD_21_5", w)

        w.cb_SMD_21_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_21_0.checkState(), "SMD_21_0")
        )
        w.cb_SMD_21_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_21_1.checkState(), "SMD_21_1")
        )
        w.cb_SMD_21_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_21_2.checkState(), "SMD_21_2")
        )
        w.cb_SMD_21_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_21_3.checkState(), "SMD_21_3")
        )
        w.cb_SMD_21_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_21_4.checkState(), "SMD_21_4")
        )
        w.cb_SMD_21_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_21_5.checkState(), "SMD_21_5")
        )

        layout_child.addWidget(w.cb_SMD_21_0)
        layout_child.addWidget(w.cb_SMD_21_1)
        layout_child.addWidget(w.cb_SMD_21_2)
        layout_child.addWidget(w.cb_SMD_21_3)
        layout_child.addWidget(w.cb_SMD_21_4)
        layout_child.addWidget(w.cb_SMD_21_5)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 22:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 23:
        w.cb_SMD_23_0 = QCheckBox("SMD_23_0", w)
        w.cb_SMD_23_1 = QCheckBox("SMD_23_1", w)
        w.cb_SMD_23_2 = QCheckBox("SMD_23_2", w)
        w.cb_SMD_23_3 = QCheckBox("SMD_23_3", w)
        w.cb_SMD_23_4 = QCheckBox("SMD_23_4", w)
        w.cb_SMD_23_5 = QCheckBox("SMD_23_5", w)
        w.cb_SMD_23_6 = QCheckBox("SMD_23_6", w)
        w.cb_Plating_23_0 = QCheckBox("Plating_23_0", w)
        w.cb_Plating_23_1 = QCheckBox("Plating_23_1", w)
        w.cb_Plating_23_2 = QCheckBox("Plating_23_2", w)
        w.cb_Plating_23_3 = QCheckBox("Plating_23_3", w)
        w.cb_Plating_23_4 = QCheckBox("Plating_23_4", w)
        w.cb_Plating_23_5 = QCheckBox("Plating_23_5", w)
        w.cb_Plating_23_6 = QCheckBox("Plating_23_6", w)
        w.cb_Plating_23_7 = QCheckBox("Plating_23_7", w)
        w.cb_Plating_23_8 = QCheckBox("Plating_23_8", w)
        w.cb_Plating_23_9 = QCheckBox("Plating_23_9", w)

        w.cb_SMD_23_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_23_0.checkState(), "SMD_23_0")
        )
        w.cb_SMD_23_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_23_1.checkState(), "SMD_23_1")
        )
        w.cb_SMD_23_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_23_2.checkState(), "SMD_23_2")
        )
        w.cb_SMD_23_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_23_3.checkState(), "SMD_23_3")
        )
        w.cb_SMD_23_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_23_4.checkState(), "SMD_23_4")
        )
        w.cb_SMD_23_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_23_5.checkState(), "SMD_23_5")
        )
        w.cb_SMD_23_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_23_6.checkState(), "SMD_23_6")
        )
        w.cb_Plating_23_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_0.checkState(), "Plating_23_0"
            )
        )
        w.cb_Plating_23_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_0.checkState(), "Plating_23_0"
            )
        )
        w.cb_Plating_23_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_1.checkState(), "Plating_23_1"
            )
        )
        w.cb_Plating_23_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_2.checkState(), "Plating_23_2"
            )
        )
        w.cb_Plating_23_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_3.checkState(), "Plating_23_3"
            )
        )
        w.cb_Plating_23_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_4.checkState(), "Plating_23_4"
            )
        )
        w.cb_Plating_23_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_5.checkState(), "Plating_23_5"
            )
        )
        w.cb_Plating_23_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_6.checkState(), "Plating_23_6"
            )
        )
        w.cb_Plating_23_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_7.checkState(), "Plating_23_7"
            )
        )
        w.cb_Plating_23_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_23_8.checkState(), "Plating_23_8"
            )
        )

        layout_child.addWidget(w.cb_SMD_23_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_23_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_23_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_23_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_23_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_23_5, 5, 1)
        layout_child.addWidget(w.cb_SMD_23_6, 6, 1)
        layout_child.addWidget(w.cb_Plating_23_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_23_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_23_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_23_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_23_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_23_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_23_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_23_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_23_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_23_9, 9, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 24:
        w.cb_SMD_24_0 = QCheckBox("SMD_24_0", w)
        w.cb_SMD_24_1 = QCheckBox("SMD_24_1", w)
        w.cb_SMD_24_2 = QCheckBox("SMD_24_2", w)
        w.cb_SMD_24_3 = QCheckBox("SMD_24_3", w)
        w.cb_SMD_24_4 = QCheckBox("SMD_24_4", w)
        w.cb_Plating_24_0 = QCheckBox("Plating_24_0", w)
        w.cb_Plating_24_1 = QCheckBox("Plating_24_1", w)
        w.cb_Plating_24_2 = QCheckBox("Plating_24_2", w)
        w.cb_Plating_24_3 = QCheckBox("Plating_24_3", w)
        w.cb_Plating_24_4 = QCheckBox("Plating_24_4", w)
        w.cb_Plating_24_5 = QCheckBox("Plating_24_5", w)
        w.cb_Plating_24_6 = QCheckBox("Plating_24_6", w)
        w.cb_Plating_24_7 = QCheckBox("Plating_24_7", w)
        w.cb_Plating_24_8 = QCheckBox("Plating_24_8", w)
        w.cb_Plating_24_9 = QCheckBox("Plating_24_9", w)
        w.cb_Plating_24_10 = QCheckBox("Plating_24_10", w)
        w.cb_Plating_24_11 = QCheckBox("Plating_24_11", w)
        w.cb_Plating_24_12 = QCheckBox("Plating_24_12", w)
        w.cb_Plating_24_13 = QCheckBox("Plating_24_13", w)
        w.cb_Plating_24_14 = QCheckBox("Plating_24_14", w)
        w.cb_Plating_24_15 = QCheckBox("Plating_24_15", w)
        w.cb_Plating_24_16 = QCheckBox("Plating_24_16", w)

        w.cb_SMD_24_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_24_0.checkState(), "SMD_24_0")
        )
        w.cb_SMD_24_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_24_1.checkState(), "SMD_24_1")
        )
        w.cb_SMD_24_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_24_2.checkState(), "SMD_24_2")
        )
        w.cb_SMD_24_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_24_3.checkState(), "SMD_24_3")
        )
        w.cb_SMD_24_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_24_4.checkState(), "SMD_24_4")
        )
        w.cb_Plating_24_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_0.checkState(), "Plating_24_0"
            )
        )
        w.cb_Plating_24_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_1.checkState(), "Plating_24_1"
            )
        )
        w.cb_Plating_24_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_2.checkState(), "Plating_24_2"
            )
        )
        w.cb_Plating_24_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_3.checkState(), "Plating_24_3"
            )
        )
        w.cb_Plating_24_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_4.checkState(), "Plating_24_4"
            )
        )
        w.cb_Plating_24_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_5.checkState(), "Plating_24_5"
            )
        )
        w.cb_Plating_24_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_6.checkState(), "Plating_24_6"
            )
        )
        w.cb_Plating_24_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_7.checkState(), "Plating_24_7"
            )
        )
        w.cb_Plating_24_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_8.checkState(), "Plating_24_8"
            )
        )
        w.cb_Plating_24_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_9.checkState(), "Plating_24_9"
            )
        )
        w.cb_Plating_24_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_10.checkState(), "Plating_24_10"
            )
        )
        w.cb_Plating_24_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_11.checkState(), "Plating_24_11"
            )
        )
        w.cb_Plating_24_12.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_12.checkState(), "Plating_24_12"
            )
        )
        w.cb_Plating_24_13.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_13.checkState(), "Plating_24_13"
            )
        )
        w.cb_Plating_24_14.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_14.checkState(), "Plating_24_14"
            )
        )
        w.cb_Plating_24_15.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_15.checkState(), "Plating_24_15"
            )
        )
        w.cb_Plating_24_16.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_24_16.checkState(), "Plating_24_16"
            )
        )

        layout_child.addWidget(w.cb_SMD_24_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_24_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_24_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_24_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_24_4, 4, 1)
        layout_child.addWidget(w.cb_Plating_24_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_24_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_24_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_24_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_24_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_24_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_24_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_24_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_24_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_24_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_24_10, 10, 0)
        layout_child.addWidget(w.cb_Plating_24_11, 11, 0)
        layout_child.addWidget(w.cb_Plating_24_12, 12, 0)
        layout_child.addWidget(w.cb_Plating_24_13, 13, 0)
        layout_child.addWidget(w.cb_Plating_24_14, 14, 0)
        layout_child.addWidget(w.cb_Plating_24_15, 15, 0)
        layout_child.addWidget(w.cb_Plating_24_16, 16, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 25:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 26:
        w.cb_SMD_26_0 = QCheckBox("SMD_26_0", w)

        w.cb_SMD_26_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_26_0.checkState(), "SMD_26_0")
        )

        layout_child.addWidget(w.cb_SMD_26_0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 27:
        w.cb_SMD_27_0 = QCheckBox("SMD_27_0", w)

        w.cb_SMD_27_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_27_0.checkState(), "SMD_27_0")
        )

        layout_child.addWidget(w.cb_SMD_27_0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 28:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 29:
        w.cb_SMD_29_0 = QCheckBox("SMD_29_0", w)
        w.cb_SMD_29_1 = QCheckBox("SMD_29_1", w)
        w.cb_SMD_29_2 = QCheckBox("SMD_29_2", w)
        w.cb_SMD_29_3 = QCheckBox("SMD_29_3", w)
        w.cb_SMD_29_4 = QCheckBox("SMD_29_4", w)
        w.cb_SMD_29_5 = QCheckBox("SMD_29_5", w)
        w.cb_Plating_29_0 = QCheckBox("Plating_29_0", w)
        w.cb_Plating_29_1 = QCheckBox("Plating_29_1", w)
        w.cb_Plating_29_2 = QCheckBox("Plating_29_2", w)
        w.cb_Plating_29_3 = QCheckBox("Plating_29_3", w)
        w.cb_Plating_29_4 = QCheckBox("Plating_29_4", w)
        w.cb_Plating_29_5 = QCheckBox("Plating_29_5", w)
        w.cb_Plating_29_6 = QCheckBox("Plating_29_6", w)
        w.cb_Plating_29_7 = QCheckBox("Plating_29_7", w)
        w.cb_Plating_29_8 = QCheckBox("Plating_29_8", w)
        w.cb_Plating_29_9 = QCheckBox("Plating_29_9", w)
        w.cb_Plating_29_10 = QCheckBox("Plating_29_10", w)
        w.cb_Plating_29_11 = QCheckBox("Plating_29_11", w)
        w.cb_Plating_29_12 = QCheckBox("Plating_29_12", w)
        w.cb_Plating_29_13 = QCheckBox("Plating_29_13", w)
        w.cb_Plating_29_14 = QCheckBox("Plating_29_14", w)
        w.cb_Plating_29_15 = QCheckBox("Plating_29_15", w)
        w.cb_Plating_29_16 = QCheckBox("Plating_29_16", w)
        w.cb_Plating_29_17 = QCheckBox("Plating_29_17", w)
        w.cb_Plating_29_18 = QCheckBox("Plating_29_18", w)

        w.cb_SMD_29_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_29_0.checkState(), "SMD_29_0")
        )
        w.cb_SMD_29_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_29_1.checkState(), "SMD_29_1")
        )
        w.cb_SMD_29_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_29_2.checkState(), "SMD_29_2")
        )
        w.cb_SMD_29_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_29_3.checkState(), "SMD_29_3")
        )
        w.cb_SMD_29_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_29_4.checkState(), "SMD_29_4")
        )
        w.cb_SMD_29_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_29_5.checkState(), "SMD_29_5")
        )
        w.cb_Plating_29_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_0.checkState(), "Plating_29_0"
            )
        )
        w.cb_Plating_29_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_1.checkState(), "Plating_29_1"
            )
        )
        w.cb_Plating_29_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_2.checkState(), "Plating_29_2"
            )
        )
        w.cb_Plating_29_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_3.checkState(), "Plating_29_3"
            )
        )
        w.cb_Plating_29_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_4.checkState(), "Plating_29_4"
            )
        )
        w.cb_Plating_29_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_5.checkState(), "Plating_29_5"
            )
        )
        w.cb_Plating_29_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_6.checkState(), "Plating_29_6"
            )
        )
        w.cb_Plating_29_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_7.checkState(), "Plating_29_7"
            )
        )
        w.cb_Plating_29_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_8.checkState(), "Plating_29_8"
            )
        )
        w.cb_Plating_29_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_9.checkState(), "Plating_29_9"
            )
        )
        w.cb_Plating_29_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_10.checkState(), "Plating_29_10"
            )
        )
        w.cb_Plating_29_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_11.checkState(), "Plating_29_11"
            )
        )
        w.cb_Plating_29_12.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_12.checkState(), "Plating_29_12"
            )
        )
        w.cb_Plating_29_13.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_13.checkState(), "Plating_29_13"
            )
        )
        w.cb_Plating_29_14.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_14.checkState(), "Plating_29_14"
            )
        )
        w.cb_Plating_29_15.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_15.checkState(), "Plating_29_15"
            )
        )
        w.cb_Plating_29_16.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_16.checkState(), "Plating_29_16"
            )
        )
        w.cb_Plating_29_17.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_17.checkState(), "Plating_29_17"
            )
        )
        w.cb_Plating_29_18.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_29_18.checkState(), "Plating_29_18"
            )
        )

        layout_child.addWidget(w.cb_SMD_29_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_29_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_29_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_29_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_29_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_29_5, 5, 1)
        layout_child.addWidget(w.cb_Plating_29_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_29_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_29_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_29_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_29_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_29_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_29_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_29_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_29_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_29_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_29_10, 10, 0)
        layout_child.addWidget(w.cb_Plating_29_11, 11, 0)
        layout_child.addWidget(w.cb_Plating_29_12, 12, 0)
        layout_child.addWidget(w.cb_Plating_29_13, 13, 0)
        layout_child.addWidget(w.cb_Plating_29_14, 14, 0)
        layout_child.addWidget(w.cb_Plating_29_15, 15, 0)
        layout_child.addWidget(w.cb_Plating_29_16, 16, 0)
        layout_child.addWidget(w.cb_Plating_29_17, 17, 0)
        layout_child.addWidget(w.cb_Plating_29_18, 18, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 30:
        w.cb_SMD_30_0 = QCheckBox("SMD_30_0", w)
        w.cb_SMD_30_1 = QCheckBox("SMD_30_1", w)
        w.cb_SMD_30_2 = QCheckBox("SMD_30_2", w)
        w.cb_SMD_30_3 = QCheckBox("SMD_30_3", w)
        w.cb_SMD_30_4 = QCheckBox("SMD_30_4", w)
        w.cb_SMD_30_5 = QCheckBox("SMD_30_5", w)
        w.cb_Plating_30_0 = QCheckBox("Plating_30_0", w)
        w.cb_Plating_30_1 = QCheckBox("Plating_30_1", w)
        w.cb_Plating_30_2 = QCheckBox("Plating_30_2", w)
        w.cb_Plating_30_3 = QCheckBox("Plating_30_3", w)
        w.cb_Plating_30_4 = QCheckBox("Plating_30_4", w)
        w.cb_Plating_30_5 = QCheckBox("Plating_30_5", w)
        w.cb_Plating_30_6 = QCheckBox("Plating_30_6", w)
        w.cb_Plating_30_7 = QCheckBox("Plating_30_7", w)
        w.cb_Plating_30_8 = QCheckBox("Plating_30_8", w)

        w.cb_SMD_30_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_30_0.checkState(), "SMD_30_0")
        )
        w.cb_SMD_30_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_30_1.checkState(), "SMD_30_1")
        )
        w.cb_SMD_30_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_30_2.checkState(), "SMD_30_2")
        )
        w.cb_SMD_30_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_30_3.checkState(), "SMD_30_3")
        )
        w.cb_SMD_30_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_30_4.checkState(), "SMD_30_4")
        )
        w.cb_SMD_30_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_30_5.checkState(), "SMD_30_5")
        )
        w.cb_Plating_30_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_0.checkState(), "Plating_30_0"
            )
        )
        w.cb_Plating_30_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_1.checkState(), "Plating_30_1"
            )
        )
        w.cb_Plating_30_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_2.checkState(), "Plating_30_2"
            )
        )
        w.cb_Plating_30_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_3.checkState(), "Plating_30_3"
            )
        )
        w.cb_Plating_30_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_4.checkState(), "Plating_30_4"
            )
        )
        w.cb_Plating_30_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_5.checkState(), "Plating_30_5"
            )
        )
        w.cb_Plating_30_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_6.checkState(), "Plating_30_6"
            )
        )
        w.cb_Plating_30_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_7.checkState(), "Plating_30_7"
            )
        )
        w.cb_Plating_30_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_30_8.checkState(), "Plating_30_8"
            )
        )

        layout_child.addWidget(w.cb_SMD_30_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_30_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_30_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_30_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_30_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_30_5, 5, 1)
        layout_child.addWidget(w.cb_Plating_30_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_30_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_30_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_30_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_30_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_30_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_30_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_30_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_30_8, 8, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 31:
        w.cb_SMD_31_0 = QCheckBox("SMD_31_0", w)
        w.cb_Plating_31_0 = QCheckBox("Plating_31_0", w)

        w.cb_SMD_31_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_31_0.checkState(), "SMD_31_0")
        )
        w.cb_Plating_31_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_31_0.checkState(), "Plating_31_0"
            )
        )

        layout_child.addWidget(w.cb_SMD_31_0, 0, 1)
        layout_child.addWidget(w.cb_Plating_31_0, 0, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 32:
        w.cb_SMD_32_0 = QCheckBox("SMD_32_0", w)
        w.cb_SMD_32_1 = QCheckBox("SMD_32_1", w)

        w.cb_SMD_32_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_32_0.checkState(), "SMD_32_0")
        )
        w.cb_SMD_32_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_32_1.checkState(), "SMD_32_1")
        )

        layout_child.addWidget(w.cb_SMD_32_0)
        layout_child.addWidget(w.cb_SMD_32_1)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 33:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 34:
        w.cb_SMD_34_0 = QCheckBox("SMD_34_0", w)

        w.cb_SMD_34_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_34_0.checkState(), "SMD_34_0")
        )

        layout_child.addWidget(w.cb_SMD_34_0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 35:
        w.cb_SMD_35_0 = QCheckBox("SMD_35_0", w)
        w.cb_SMD_35_1 = QCheckBox("SMD_35_1", w)
        w.cb_SMD_35_2 = QCheckBox("SMD_35_2", w)
        w.cb_SMD_35_3 = QCheckBox("SMD_35_3", w)
        w.cb_SMD_35_4 = QCheckBox("SMD_35_4", w)
        w.cb_SMD_35_5 = QCheckBox("SMD_35_5", w)
        w.cb_SMD_35_6 = QCheckBox("SMD_35_6", w)
        w.cb_Plating_35_0 = QCheckBox("Plating_35_0", w)
        w.cb_Plating_35_1 = QCheckBox("Plating_35_1", w)
        w.cb_Plating_35_2 = QCheckBox("Plating_35_2", w)
        w.cb_Plating_35_3 = QCheckBox("Plating_35_3", w)
        w.cb_Plating_35_4 = QCheckBox("Plating_35_4", w)
        w.cb_Plating_35_5 = QCheckBox("Plating_35_5", w)
        w.cb_Plating_35_6 = QCheckBox("Plating_35_6", w)
        w.cb_Plating_35_7 = QCheckBox("Plating_35_7", w)
        w.cb_Plating_35_8 = QCheckBox("Plating_35_8", w)
        w.cb_Plating_35_9 = QCheckBox("Plating_35_9", w)
        w.cb_Plating_35_10 = QCheckBox("Plating_35_10", w)
        w.cb_Plating_35_11 = QCheckBox("Plating_35_11", w)

        w.cb_SMD_35_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_35_0.checkState(), "SMD_35_0")
        )
        w.cb_SMD_35_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_35_1.checkState(), "SMD_35_1")
        )
        w.cb_SMD_35_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_35_2.checkState(), "SMD_35_2")
        )
        w.cb_SMD_35_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_35_3.checkState(), "SMD_35_3")
        )
        w.cb_SMD_35_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_35_4.checkState(), "SMD_35_4")
        )
        w.cb_SMD_35_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_35_5.checkState(), "SMD_35_5")
        )
        w.cb_SMD_35_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_35_6.checkState(), "SMD_35_6")
        )
        w.cb_Plating_35_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_0.checkState(), "Plating_35_0"
            )
        )
        w.cb_Plating_35_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_1.checkState(), "Plating_35_1"
            )
        )
        w.cb_Plating_35_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_2.checkState(), "Plating_35_2"
            )
        )
        w.cb_Plating_35_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_3.checkState(), "Plating_35_3"
            )
        )
        w.cb_Plating_35_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_4.checkState(), "Plating_35_4"
            )
        )
        w.cb_Plating_35_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_5.checkState(), "Plating_35_5"
            )
        )
        w.cb_Plating_35_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_6.checkState(), "Plating_35_6"
            )
        )
        w.cb_Plating_35_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_7.checkState(), "Plating_35_7"
            )
        )
        w.cb_Plating_35_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_8.checkState(), "Plating_35_8"
            )
        )
        w.cb_Plating_35_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_9.checkState(), "Plating_35_9"
            )
        )
        w.cb_Plating_35_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_10.checkState(), "Plating_35_10"
            )
        )
        w.cb_Plating_35_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(
                w.cb_Plating_35_11.checkState(), "Plating_35_11"
            )
        )

        layout_child.addWidget(w.cb_SMD_35_0, 0, 1)
        layout_child.addWidget(w.cb_SMD_35_1, 1, 1)
        layout_child.addWidget(w.cb_SMD_35_2, 2, 1)
        layout_child.addWidget(w.cb_SMD_35_3, 3, 1)
        layout_child.addWidget(w.cb_SMD_35_4, 4, 1)
        layout_child.addWidget(w.cb_SMD_35_5, 5, 1)
        layout_child.addWidget(w.cb_SMD_35_6, 6, 1)
        layout_child.addWidget(w.cb_Plating_35_0, 0, 0)
        layout_child.addWidget(w.cb_Plating_35_1, 1, 0)
        layout_child.addWidget(w.cb_Plating_35_2, 2, 0)
        layout_child.addWidget(w.cb_Plating_35_3, 3, 0)
        layout_child.addWidget(w.cb_Plating_35_4, 4, 0)
        layout_child.addWidget(w.cb_Plating_35_5, 5, 0)
        layout_child.addWidget(w.cb_Plating_35_6, 6, 0)
        layout_child.addWidget(w.cb_Plating_35_7, 7, 0)
        layout_child.addWidget(w.cb_Plating_35_8, 8, 0)
        layout_child.addWidget(w.cb_Plating_35_9, 9, 0)
        layout_child.addWidget(w.cb_Plating_35_10, 10, 0)
        layout_child.addWidget(w.cb_Plating_35_11, 11, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    return layout
