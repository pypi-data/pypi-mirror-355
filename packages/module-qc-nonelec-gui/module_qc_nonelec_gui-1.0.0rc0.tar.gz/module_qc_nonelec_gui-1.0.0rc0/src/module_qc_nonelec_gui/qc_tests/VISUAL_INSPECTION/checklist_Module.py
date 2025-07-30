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
        w.cb_Wire_0_0 = QCheckBox("Wire_0_0", w)
        w.cb_Wire_0_1 = QCheckBox("Wire_0_1", w)
        w.cb_Wire_0_2 = QCheckBox("Wire_0_2", w)
        w.cb_Wire_0_3 = QCheckBox("Wire_0_3", w)
        w.cb_Wire_0_4 = QCheckBox("Wire_0_4", w)
        w.cb_Wire_0_5 = QCheckBox("Wire_0_5", w)
        w.cb_Wire_0_6 = QCheckBox("Wire_0_6", w)
        w.cb_Wire_0_7 = QCheckBox("Wire_0_7", w)
        w.cb_Wire_0_8 = QCheckBox("Wire_0_8", w)
        w.cb_Wire_0_9 = QCheckBox("Wire_0_9", w)
        w.cb_Wire_0_10 = QCheckBox("Wire_0_10", w)

        w.cb_Wire_0_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_0.checkState(), "Wire_0_0")
        )
        w.cb_Wire_0_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_1.checkState(), "Wire_0_1")
        )
        w.cb_Wire_0_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_2.checkState(), "Wire_0_2")
        )
        w.cb_Wire_0_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_3.checkState(), "Wire_0_3")
        )
        w.cb_Wire_0_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_4.checkState(), "Wire_0_4")
        )
        w.cb_Wire_0_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_5.checkState(), "Wire_0_5")
        )
        w.cb_Wire_0_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_6.checkState(), "Wire_0_6")
        )
        w.cb_Wire_0_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_7.checkState(), "Wire_0_7")
        )
        w.cb_Wire_0_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_8.checkState(), "Wire_0_8")
        )
        w.cb_Wire_0_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_9.checkState(), "Wire_0_9")
        )
        w.cb_Wire_0_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_0_10.checkState(), "Wire_0_10")
        )

        layout_child.addWidget(w.cb_Wire_0_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_0_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_0_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_0_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_0_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_0_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_0_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_0_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_0_8, 8, 0)
        layout_child.addWidget(w.cb_Wire_0_9, 9, 0)
        layout_child.addWidget(w.cb_Wire_0_10, 10, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 1:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 2:
        w.cb_Wire_2_0 = QCheckBox("Wire_2_0", w)

        w.cb_Wire_2_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_2_0.checkState(), "Wire_2_0")
        )

        layout_child.addWidget(w.cb_Wire_2_0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 3:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 4:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 5:
        w.cb_Wire_5_0 = QCheckBox("Wire_5_0", w)
        w.cb_Wire_5_1 = QCheckBox("Wire_5_1", w)
        w.cb_Wire_5_2 = QCheckBox("Wire_5_2", w)
        w.cb_Wire_5_3 = QCheckBox("Wire_5_3", w)
        w.cb_Wire_5_4 = QCheckBox("Wire_5_4", w)
        w.cb_Wire_5_5 = QCheckBox("Wire_5_5", w)
        w.cb_Wire_5_6 = QCheckBox("Wire_5_6", w)
        w.cb_Wire_5_7 = QCheckBox("Wire_5_7", w)
        w.cb_Wire_5_8 = QCheckBox("Wire_5_8", w)

        w.cb_Wire_5_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_0.checkState(), "Wire_5_0")
        )
        w.cb_Wire_5_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_1.checkState(), "Wire_5_1")
        )
        w.cb_Wire_5_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_2.checkState(), "Wire_5_2")
        )
        w.cb_Wire_5_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_3.checkState(), "Wire_5_3")
        )
        w.cb_Wire_5_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_4.checkState(), "Wire_5_4")
        )
        w.cb_Wire_5_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_5.checkState(), "Wire_5_5")
        )
        w.cb_Wire_5_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_6.checkState(), "Wire_5_6")
        )
        w.cb_Wire_5_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_7.checkState(), "Wire_5_7")
        )
        w.cb_Wire_5_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_5_8.checkState(), "Wire_5_8")
        )

        layout_child.addWidget(w.cb_Wire_5_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_5_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_5_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_5_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_5_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_5_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_5_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_5_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_5_8, 8, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 6:
        w.cb_Wire_6_0 = QCheckBox("Wire_6_0", w)
        w.cb_Wire_6_1 = QCheckBox("Wire_6_1", w)
        w.cb_Wire_6_2 = QCheckBox("Wire_6_2", w)
        w.cb_Wire_6_3 = QCheckBox("Wire_6_3", w)
        w.cb_Wire_6_4 = QCheckBox("Wire_6_4", w)
        w.cb_Wire_6_5 = QCheckBox("Wire_6_5", w)
        w.cb_Wire_6_6 = QCheckBox("Wire_6_6", w)
        w.cb_Wire_6_7 = QCheckBox("Wire_6_7", w)
        w.cb_Wire_6_8 = QCheckBox("Wire_6_8", w)
        w.cb_Wire_6_9 = QCheckBox("Wire_6_9", w)
        w.cb_Wire_6_10 = QCheckBox("Wire_6_10", w)

        w.cb_Wire_6_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_0.checkState(), "Wire_6_0")
        )
        w.cb_Wire_6_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_1.checkState(), "Wire_6_1")
        )
        w.cb_Wire_6_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_2.checkState(), "Wire_6_2")
        )
        w.cb_Wire_6_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_3.checkState(), "Wire_6_3")
        )
        w.cb_Wire_6_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_4.checkState(), "Wire_6_4")
        )
        w.cb_Wire_6_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_5.checkState(), "Wire_6_5")
        )
        w.cb_Wire_6_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_6.checkState(), "Wire_6_6")
        )
        w.cb_Wire_6_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_7.checkState(), "Wire_6_7")
        )
        w.cb_Wire_6_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_8.checkState(), "Wire_6_8")
        )
        w.cb_Wire_6_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_9.checkState(), "Wire_6_9")
        )
        w.cb_Wire_6_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_6_10.checkState(), "Wire_6_10")
        )

        layout_child.addWidget(w.cb_Wire_6_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_6_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_6_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_6_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_6_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_6_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_6_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_6_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_6_8, 8, 0)
        layout_child.addWidget(w.cb_Wire_6_9, 9, 0)
        layout_child.addWidget(w.cb_Wire_6_10, 10, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 7:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 8:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 9:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 10:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 11:
        w.cb_Wire_11_0 = QCheckBox("Wire_11_0", w)
        w.cb_Wire_11_1 = QCheckBox("Wire_11_1", w)
        w.cb_Wire_11_2 = QCheckBox("Wire_11_2", w)
        w.cb_Wire_11_3 = QCheckBox("Wire_11_3", w)
        w.cb_Wire_11_4 = QCheckBox("Wire_11_4", w)
        w.cb_Wire_11_5 = QCheckBox("Wire_11_5", w)
        w.cb_Wire_11_6 = QCheckBox("Wire_11_6", w)
        w.cb_Wire_11_7 = QCheckBox("Wire_11_7", w)
        w.cb_Wire_11_8 = QCheckBox("Wire_11_8", w)
        w.cb_Wire_11_9 = QCheckBox("Wire_11_9", w)

        w.cb_Wire_11_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_0.checkState(), "Wire_11_0")
        )
        w.cb_Wire_11_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_1.checkState(), "Wire_11_1")
        )
        w.cb_Wire_11_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_2.checkState(), "Wire_11_2")
        )
        w.cb_Wire_11_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_3.checkState(), "Wire_11_3")
        )
        w.cb_Wire_11_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_4.checkState(), "Wire_11_4")
        )
        w.cb_Wire_11_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_5.checkState(), "Wire_11_5")
        )
        w.cb_Wire_11_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_6.checkState(), "Wire_11_6")
        )
        w.cb_Wire_11_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_7.checkState(), "Wire_11_7")
        )
        w.cb_Wire_11_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_8.checkState(), "Wire_11_8")
        )
        w.cb_Wire_11_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_11_9.checkState(), "Wire_11_9")
        )

        layout_child.addWidget(w.cb_Wire_11_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_11_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_11_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_11_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_11_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_11_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_11_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_11_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_11_8, 8, 0)
        layout_child.addWidget(w.cb_Wire_11_9, 9, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 12:
        w.cb_Wire_12_0 = QCheckBox("Wire_12_0", w)
        w.cb_Wire_12_1 = QCheckBox("Wire_12_1", w)
        w.cb_Wire_12_2 = QCheckBox("Wire_12_2", w)
        w.cb_Wire_12_3 = QCheckBox("Wire_12_3", w)
        w.cb_Wire_12_4 = QCheckBox("Wire_12_4", w)
        w.cb_Wire_12_5 = QCheckBox("Wire_12_5", w)
        w.cb_Wire_12_6 = QCheckBox("Wire_12_6", w)
        w.cb_Wire_12_7 = QCheckBox("Wire_12_7", w)
        w.cb_Wire_12_8 = QCheckBox("Wire_12_8", w)

        w.cb_Wire_12_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_0.checkState(), "Wire_12_0")
        )
        w.cb_Wire_12_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_1.checkState(), "Wire_12_1")
        )
        w.cb_Wire_12_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_2.checkState(), "Wire_12_2")
        )
        w.cb_Wire_12_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_3.checkState(), "Wire_12_3")
        )
        w.cb_Wire_12_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_4.checkState(), "Wire_12_4")
        )
        w.cb_Wire_12_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_5.checkState(), "Wire_12_5")
        )
        w.cb_Wire_12_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_6.checkState(), "Wire_12_6")
        )
        w.cb_Wire_12_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_7.checkState(), "Wire_12_7")
        )
        w.cb_Wire_12_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_12_8.checkState(), "Wire_12_8")
        )

        layout_child.addWidget(w.cb_Wire_12_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_12_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_12_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_12_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_12_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_12_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_12_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_12_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_12_8, 8, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 13:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 14:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 15:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 16:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 17:
        w.cb_Wire_17_0 = QCheckBox("Wire_17_0", w)
        w.cb_Wire_17_1 = QCheckBox("Wire_17_1", w)
        w.cb_Wire_17_2 = QCheckBox("Wire_17_2", w)
        w.cb_Wire_17_3 = QCheckBox("Wire_17_3", w)
        w.cb_Wire_17_4 = QCheckBox("Wire_17_4", w)
        w.cb_Wire_17_5 = QCheckBox("Wire_17_5", w)
        w.cb_Wire_17_6 = QCheckBox("Wire_17_6", w)
        w.cb_Wire_17_7 = QCheckBox("Wire_17_7", w)
        w.cb_Wire_17_8 = QCheckBox("Wire_17_8", w)
        w.cb_Wire_17_9 = QCheckBox("Wire_17_9", w)
        w.cb_Wire_17_10 = QCheckBox("Wire_17_10", w)
        w.cb_Wire_17_11 = QCheckBox("Wire_17_11", w)

        w.cb_Wire_17_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_0.checkState(), "Wire_17_0")
        )
        w.cb_Wire_17_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_1.checkState(), "Wire_17_1")
        )
        w.cb_Wire_17_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_2.checkState(), "Wire_17_2")
        )
        w.cb_Wire_17_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_3.checkState(), "Wire_17_3")
        )
        w.cb_Wire_17_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_4.checkState(), "Wire_17_4")
        )
        w.cb_Wire_17_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_5.checkState(), "Wire_17_5")
        )
        w.cb_Wire_17_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_6.checkState(), "Wire_17_6")
        )
        w.cb_Wire_17_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_7.checkState(), "Wire_17_7")
        )
        w.cb_Wire_17_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_8.checkState(), "Wire_17_8")
        )
        w.cb_Wire_17_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_9.checkState(), "Wire_17_9")
        )
        w.cb_Wire_17_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_10.checkState(), "Wire_17_10")
        )
        w.cb_Wire_17_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_17_11.checkState(), "Wire_17_11")
        )

        layout_child.addWidget(w.cb_Wire_17_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_17_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_17_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_17_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_17_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_17_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_17_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_17_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_17_8, 8, 0)
        layout_child.addWidget(w.cb_Wire_17_9, 9, 0)
        layout_child.addWidget(w.cb_Wire_17_10, 10, 0)
        layout_child.addWidget(w.cb_Wire_17_11, 11, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 18:
        w.cb_Wire_18_0 = QCheckBox("Wire_18_0", w)
        w.cb_Wire_18_1 = QCheckBox("Wire_18_1", w)
        w.cb_Wire_18_2 = QCheckBox("Wire_18_2", w)
        w.cb_Wire_18_3 = QCheckBox("Wire_18_3", w)
        w.cb_Wire_18_4 = QCheckBox("Wire_18_4", w)
        w.cb_Wire_18_5 = QCheckBox("Wire_18_5", w)
        w.cb_Wire_18_6 = QCheckBox("Wire_18_6", w)
        w.cb_Wire_18_7 = QCheckBox("Wire_18_7", w)
        w.cb_Wire_18_8 = QCheckBox("Wire_18_8", w)
        w.cb_Wire_18_9 = QCheckBox("Wire_18_9", w)
        w.cb_Wire_18_10 = QCheckBox("Wire_18_10", w)
        w.cb_Wire_18_11 = QCheckBox("Wire_18_11", w)

        w.cb_Wire_18_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_0.checkState(), "Wire_18_0")
        )
        w.cb_Wire_18_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_1.checkState(), "Wire_18_1")
        )
        w.cb_Wire_18_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_2.checkState(), "Wire_18_2")
        )
        w.cb_Wire_18_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_3.checkState(), "Wire_18_3")
        )
        w.cb_Wire_18_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_4.checkState(), "Wire_18_4")
        )
        w.cb_Wire_18_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_5.checkState(), "Wire_18_5")
        )
        w.cb_Wire_18_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_6.checkState(), "Wire_18_6")
        )
        w.cb_Wire_18_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_7.checkState(), "Wire_18_7")
        )
        w.cb_Wire_18_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_8.checkState(), "Wire_18_8")
        )
        w.cb_Wire_18_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_9.checkState(), "Wire_18_9")
        )
        w.cb_Wire_18_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_10.checkState(), "Wire_18_10")
        )
        w.cb_Wire_18_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_18_11.checkState(), "Wire_18_11")
        )

        layout_child.addWidget(w.cb_Wire_18_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_18_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_18_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_18_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_18_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_18_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_18_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_18_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_18_8, 8, 0)
        layout_child.addWidget(w.cb_Wire_18_9, 9, 0)
        layout_child.addWidget(w.cb_Wire_18_10, 10, 0)
        layout_child.addWidget(w.cb_Wire_18_11, 11, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 19:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 20:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 21:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 22:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 23:
        w.cb_Wire_23_0 = QCheckBox("Wire_23_0", w)
        w.cb_Wire_23_1 = QCheckBox("Wire_23_1", w)
        w.cb_Wire_23_2 = QCheckBox("Wire_23_2", w)
        w.cb_Wire_23_3 = QCheckBox("Wire_23_3", w)
        w.cb_Wire_23_4 = QCheckBox("Wire_23_4", w)
        w.cb_Wire_23_5 = QCheckBox("Wire_23_5", w)
        w.cb_Wire_23_6 = QCheckBox("Wire_23_6", w)
        w.cb_Wire_23_7 = QCheckBox("Wire_23_7", w)
        w.cb_Wire_23_8 = QCheckBox("Wire_23_8", w)

        w.cb_Wire_23_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_0.checkState(), "Wire_23_0")
        )
        w.cb_Wire_23_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_0.checkState(), "Wire_23_1")
        )
        w.cb_Wire_23_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_1.checkState(), "Wire_23_2")
        )
        w.cb_Wire_23_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_2.checkState(), "Wire_23_3")
        )
        w.cb_Wire_23_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_3.checkState(), "Wire_23_4")
        )
        w.cb_Wire_23_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_4.checkState(), "Wire_23_5")
        )
        w.cb_Wire_23_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_5.checkState(), "Wire_23_6")
        )
        w.cb_Wire_23_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_6.checkState(), "Wire_23_7")
        )
        w.cb_Wire_23_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_23_7.checkState(), "Wire_23_8")
        )

        layout_child.addWidget(w.cb_Wire_23_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_23_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_23_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_23_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_23_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_23_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_23_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_23_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_23_8, 8, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 24:
        w.cb_Wire_24_0 = QCheckBox("Wire_24_0", w)
        w.cb_Wire_24_1 = QCheckBox("Wire_24_1", w)
        w.cb_Wire_24_2 = QCheckBox("Wire_24_2", w)
        w.cb_Wire_24_3 = QCheckBox("Wire_24_3", w)
        w.cb_Wire_24_4 = QCheckBox("Wire_24_4", w)
        w.cb_Wire_24_5 = QCheckBox("Wire_24_5", w)
        w.cb_Wire_24_6 = QCheckBox("Wire_24_6", w)
        w.cb_Wire_24_7 = QCheckBox("Wire_24_7", w)
        w.cb_Wire_24_8 = QCheckBox("Wire_24_8", w)
        w.cb_Wire_24_9 = QCheckBox("Wire_24_9", w)
        w.cb_Wire_24_10 = QCheckBox("Wire_24_10", w)
        w.cb_Wire_24_11 = QCheckBox("Wire_24_11", w)

        w.cb_Wire_24_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_0.checkState(), "Wire_24_0")
        )
        w.cb_Wire_24_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_1.checkState(), "Wire_24_1")
        )
        w.cb_Wire_24_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_2.checkState(), "Wire_24_2")
        )
        w.cb_Wire_24_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_3.checkState(), "Wire_24_3")
        )
        w.cb_Wire_24_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_4.checkState(), "Wire_24_4")
        )
        w.cb_Wire_24_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_5.checkState(), "Wire_24_5")
        )
        w.cb_Wire_24_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_6.checkState(), "Wire_24_6")
        )
        w.cb_Wire_24_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_7.checkState(), "Wire_24_7")
        )
        w.cb_Wire_24_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_8.checkState(), "Wire_24_8")
        )
        w.cb_Wire_24_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_9.checkState(), "Wire_24_9")
        )
        w.cb_Wire_24_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_10.checkState(), "Wire_24_10")
        )
        w.cb_Wire_24_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_24_11.checkState(), "Wire_24_11")
        )

        layout_child.addWidget(w.cb_Wire_24_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_24_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_24_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_24_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_24_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_24_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_24_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_24_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_24_8, 8, 0)
        layout_child.addWidget(w.cb_Wire_24_9, 9, 0)
        layout_child.addWidget(w.cb_Wire_24_10, 10, 0)
        layout_child.addWidget(w.cb_Wire_24_11, 11, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 25:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 26:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 27:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 28:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 29:
        w.cb_Wire_29_0 = QCheckBox("Wire_29_0", w)
        w.cb_Wire_29_1 = QCheckBox("Wire_29_1", w)
        w.cb_Wire_29_2 = QCheckBox("Wire_29_2", w)
        w.cb_Wire_29_3 = QCheckBox("Wire_29_3", w)
        w.cb_Wire_29_4 = QCheckBox("Wire_29_4", w)
        w.cb_Wire_29_5 = QCheckBox("Wire_29_5", w)
        w.cb_Wire_29_6 = QCheckBox("Wire_29_6", w)
        w.cb_Wire_29_7 = QCheckBox("Wire_29_7", w)
        w.cb_Wire_29_8 = QCheckBox("Wire_29_8", w)
        w.cb_Wire_29_9 = QCheckBox("Wire_29_9", w)
        w.cb_Wire_29_10 = QCheckBox("Wire_29_10", w)
        w.cb_Wire_29_11 = QCheckBox("Wire_29_11", w)

        w.cb_Wire_29_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_0.checkState(), "Wire_29_0")
        )
        w.cb_Wire_29_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_1.checkState(), "Wire_29_1")
        )
        w.cb_Wire_29_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_2.checkState(), "Wire_29_2")
        )
        w.cb_Wire_29_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_3.checkState(), "Wire_29_3")
        )
        w.cb_Wire_29_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_4.checkState(), "Wire_29_4")
        )
        w.cb_Wire_29_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_5.checkState(), "Wire_29_5")
        )
        w.cb_Wire_29_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_6.checkState(), "Wire_29_6")
        )
        w.cb_Wire_29_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_7.checkState(), "Wire_29_7")
        )
        w.cb_Wire_29_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_8.checkState(), "Wire_29_8")
        )
        w.cb_Wire_29_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_9.checkState(), "Wire_29_9")
        )
        w.cb_Wire_29_10.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_10.checkState(), "Wire_29_10")
        )
        w.cb_Wire_29_11.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_29_11.checkState(), "Wire_29_11")
        )

        layout_child.addWidget(w.cb_Wire_29_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_29_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_29_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_29_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_29_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_29_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_29_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_29_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_29_8, 8, 0)
        layout_child.addWidget(w.cb_Wire_29_9, 9, 0)
        layout_child.addWidget(w.cb_Wire_29_10, 10, 0)
        layout_child.addWidget(w.cb_Wire_29_11, 11, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 30:
        w.cb_Wire_30_0 = QCheckBox("Wire_30_0", w)
        w.cb_Wire_30_1 = QCheckBox("Wire_30_1", w)
        w.cb_Wire_30_2 = QCheckBox("Wire_30_2", w)
        w.cb_Wire_30_3 = QCheckBox("Wire_30_3", w)
        w.cb_Wire_30_4 = QCheckBox("Wire_30_4", w)
        w.cb_Wire_30_5 = QCheckBox("Wire_30_5", w)
        w.cb_Wire_30_6 = QCheckBox("Wire_30_6", w)

        w.cb_Wire_30_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_30_0.checkState(), "Wire_30_0")
        )
        w.cb_Wire_30_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_30_1.checkState(), "Wire_30_1")
        )
        w.cb_Wire_30_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_30_2.checkState(), "Wire_30_2")
        )
        w.cb_Wire_30_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_30_3.checkState(), "Wire_30_3")
        )
        w.cb_Wire_30_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_30_4.checkState(), "Wire_30_4")
        )
        w.cb_Wire_30_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_30_5.checkState(), "Wire_30_5")
        )
        w.cb_Wire_30_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_30_6.checkState(), "Wire_30_6")
        )

        layout_child.addWidget(w.cb_Wire_30_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_30_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_30_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_30_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_30_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_30_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_30_6, 6, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 31:
        w.cb_Wire_31_0 = QCheckBox("Wire_31_0", w)

        w.cb_SMD_31_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_SMD_31_0.checkState(), "SMD_31_0")
        )

        layout_child.addWidget(w.cb_Wire_31_0, 0, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 32:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 33:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 34:
        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    if page == 35:
        w.cb_Wire_35_0 = QCheckBox("Wire_35_0", w)
        w.cb_Wire_35_1 = QCheckBox("Wire_35_1", w)
        w.cb_Wire_35_2 = QCheckBox("Wire_35_2", w)
        w.cb_Wire_35_3 = QCheckBox("Wire_35_3", w)
        w.cb_Wire_35_4 = QCheckBox("Wire_35_4", w)
        w.cb_Wire_35_5 = QCheckBox("Wire_35_5", w)
        w.cb_Wire_35_6 = QCheckBox("Wire_35_6", w)
        w.cb_Wire_35_7 = QCheckBox("Wire_35_7", w)
        w.cb_Wire_35_8 = QCheckBox("Wire_35_8", w)
        w.cb_Wire_35_9 = QCheckBox("Wire_35_9", w)

        w.cb_Wire_35_0.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_0.checkState(), "Wire_35_0")
        )
        w.cb_Wire_35_1.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_1.checkState(), "Wire_35_1")
        )
        w.cb_Wire_35_2.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_2.checkState(), "Wire_35_2")
        )
        w.cb_Wire_35_3.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_3.checkState(), "Wire_35_3")
        )
        w.cb_Wire_35_4.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_4.checkState(), "Wire_35_4")
        )
        w.cb_Wire_35_5.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_5.checkState(), "Wire_35_5")
        )
        w.cb_Wire_35_6.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_6.checkState(), "Wire_35_6")
        )
        w.cb_Wire_35_7.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_7.checkState(), "Wire_35_7")
        )
        w.cb_Wire_35_8.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_8.checkState(), "Wire_35_8")
        )
        w.cb_Wire_35_9.stateChanged.connect(
            lambda: w.checkBoxChangeAction(w.cb_Wire_35_9.checkState(), "Wire_35_9")
        )

        layout_child.addWidget(w.cb_Wire_35_0, 0, 0)
        layout_child.addWidget(w.cb_Wire_35_1, 1, 0)
        layout_child.addWidget(w.cb_Wire_35_2, 2, 0)
        layout_child.addWidget(w.cb_Wire_35_3, 3, 0)
        layout_child.addWidget(w.cb_Wire_35_4, 4, 0)
        layout_child.addWidget(w.cb_Wire_35_5, 5, 0)
        layout_child.addWidget(w.cb_Wire_35_6, 6, 0)
        layout_child.addWidget(w.cb_Wire_35_7, 7, 0)
        layout_child.addWidget(w.cb_Wire_35_8, 8, 0)
        layout_child.addWidget(w.cb_Wire_35_9, 9, 0)

        layout.addLayout(layout_child)
        layout.addLayout(commonpart_gen(w))

    return layout
