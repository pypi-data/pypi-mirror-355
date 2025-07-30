""" """

import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))
import napari
import numpy as np
import pyqtgraph as pg
from magicgui.widgets import (
    CheckBox,
    ComboBox,
    Container,
    PushButton,
    SpinBox,
)
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from napari_hsi_analysis.modules.functions import RGB_to_hex


class PCAWidget(QWidget):
    def __init__(self, viewer: napari.Viewer, data, plot_widget):
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.plot_widget = plot_widget
        scroll = QScrollArea()  # Creiamo lo scroll area
        scroll.setWidgetResizable(True)
        content_widget = (
            QWidget()
        )  # Creiamo un widget contenitore per i nostri elementi
        content_layout = QVBoxLayout(content_widget)  # Layout per i widget
        self.createUI(content_layout)  # Aggiungiamo i widget
        scroll.setWidget(
            content_widget
        )  # Impostiamo il widget nello scroll area
        main_layout = QVBoxLayout(self)  # Layout principale della finestra
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
        self.hex_reshaped = np.zeros(1)

    def createUI(self, layout):
        PCA_box = QGroupBox("PCA")
        PCA_main_layout = QVBoxLayout()
        # - - - pca data - - -
        PCA_layout_data = QHBoxLayout()
        self.reduced_dataset = CheckBox(text="Apply to reduced dataset")
        self.modes_combobox = ComboBox(
            choices=self.data.modes, label="Select the imaging mode"
        )  # DROPDOWN FOR CALIBRATION
        self.n_components = SpinBox(
            min=1, max=100, value=10, step=1, name="Number of components"
        )

        PCA_perform_btn = PushButton(text="Perform PCA")
        PCA_perform_btn.clicked.connect(self.PCA_perform_btn_f)
        PCA_layout_data.addWidget(
            Container(
                widgets=[
                    self.reduced_dataset,
                    self.modes_combobox,
                    self.n_components,
                    PCA_perform_btn,
                ]
            ).native
        )

        # - - - pca variables - - -
        PCA_layout_plot_var = QHBoxLayout()
        self.x_axis = SpinBox(min=1, max=100, value=1, step=1, name="X axis")
        self.y_axis = SpinBox(min=1, max=100, value=2, step=1, name="Y axis")

        PCA_show_plot_btn = PushButton(text="Show PCA scatterplot")
        PCA_show_plot_btn.clicked.connect(self.PCA_show_plot_btn_f)
        PCA_layout_plot_var.addWidget(
            Container(
                widgets=[self.x_axis, self.y_axis, PCA_show_plot_btn]
            ).native
        )

        self.pca_plot = pg.PlotWidget()
        self.plot_widget.setup_scatterplot(self.pca_plot)

        # Add control buttons for scatter plot interaction
        btn_layout = QHBoxLayout()

        for icon, func in [
            ("fa5s.home", lambda: self.pca_plot.getViewBox().autoRange()),
            (
                "fa5s.draw-polygon",
                lambda: self.plot_widget.polygon_selection(self.pca_plot),
            ),
            ("ri.add-box-fill", self.handle_selection),
            (
                "mdi6.image-edit",
                lambda: self.plot_widget.save_image_button(self.pca_plot),
            ),
        ]:
            btn = self.plot_widget.create_button(icon)
            btn.clicked.connect(func)
            btn_layout.addWidget(btn)

        self.point_size = SpinBox(
            min=1, max=100, value=1, step=1, name="Point size"
        )
        btn_layout.addSpacing(30)
        btn_layout.addWidget(Container(widgets=[self.point_size]).native)
        PCA_main_layout.addLayout(btn_layout)
        PCA_main_layout.addWidget(self.pca_plot)

        """
        PCA_layout_plot = QVBoxLayout()
        self.PCA_select_btn = PushButton(text ="Selezione Poligonale")
        #self.PCA_select_btn.clicked.connect(self.plot_widget.PCA_select_btn_f)
        self.PCA_print_btn = PushButton(text ="Stampa Selezionati")
        #self.PCA_print_btn.clicked.connect(self.plot_widget.PCA_print_btn_f)
        self.PCA_home_btn = PushButton(text ="Home")

        self.PCA_plot_widget = pg.PlotWidget()
        self.PCA_plot_widget.setMinimumSize(400, 400)
        PCA_layout_plot.addWidget(Container(widgets=[self.PCA_select_btn, self.PCA_print_btn, self.PCA_home_btn, self.PCA_plot_widget]).native)
        self.PCA_home_btn.clicked.connect(self.PCA_plot_widget.getViewBox().autoRange())
        """
        PCA_main_layout.addLayout(PCA_layout_data)
        PCA_main_layout.addLayout(PCA_layout_plot_var)
        # PCA_main_layout.addLayout(PCA_layout_plot)
        PCA_box.setLayout(PCA_main_layout)
        layout.addWidget(PCA_box)
        layout.addStretch()

    def PCA_perform_btn_f(self):
        self.data.mode = self.modes_combobox.value
        if self.reduced_dataset.value:
            self.PCA_dataset = self.data.hypercubes_red[self.data.mode]
        else:
            self.PCA_dataset = self.data.hypercubes[self.data.mode]
        self.data.pca_analysis(
            self.PCA_dataset, self.data.mode, self.n_components.value
        )

    def PCA_show_plot_btn_f(self):
        """Plot UMAP scatter plot"""
        mode = self.modes_combobox.value
        pca_xaxis = self.x_axis.value - 1
        pca_yaxis = self.y_axis.value - 1
        H_PCA_reshaped = self.data.pca_maps[self.modes_combobox.value].reshape(
            -1, self.n_components.value
        )
        self.H_PCA_reshaped_selected = np.stack(
            (H_PCA_reshaped[:, pca_xaxis], H_PCA_reshaped[:, pca_yaxis])
        ).T

        if self.reduced_dataset.value:
            colors = RGB_to_hex(self.data.rgb_red[mode])

        else:
            colors = RGB_to_hex(self.data.rgb[mode])

        print("Colors: \n", colors.reshape(-1))
        self.points = []
        self.plot_widget.show_scatterplot(
            self.pca_plot,
            self.H_PCA_reshaped_selected,
            colors.reshape(-1),
            self.points,
            self.point_size.value,
        )

    def handle_selection(self):
        """Handle polygon selection and create label layer"""
        mode = self.modes_combobox.value
        if self.reduced_dataset.value:
            dataset = self.data.hypercubes_red[mode]
            self.points = []

        else:
            dataset = self.data.hypercubes[mode]
        self.plot_widget.show_selected_points(
            self.H_PCA_reshaped_selected,
            dataset,
            mode,
            self.points,
        )
