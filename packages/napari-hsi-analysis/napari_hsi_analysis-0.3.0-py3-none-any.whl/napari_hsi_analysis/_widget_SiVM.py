""" """

import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))
import napari
import numpy as np
from magicgui.widgets import (
    CheckBox,
    ComboBox,
    Container,
    FloatSpinBox,
    PushButton,
    Select,
    SpinBox,
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from napari.utils.notifications import show_info
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SiVMWidget(QWidget):
    """ """

    def __init__(self, viewer: napari.Viewer, data, plot_widget):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.plot_widget = plot_widget
        self.init_ui()

    def init_ui(self):
        """ """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        sivm_group = self.build_sivm_group()
        content_layout.addWidget(sivm_group)
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def build_sivm_group(self):
        """ """
        sivm_box = QGroupBox("SiVM")
        sivm_layout = QVBoxLayout()

        sivm_layout.addLayout(self.create_sivm_controls())
        sivm_layout.addLayout(self.create_sivm_analysis())
        sivm_layout.addLayout(self.create_spectrum_area())
        sivm_layout.addLayout(self.create_nnls())

        sivm_box.setLayout(sivm_layout)
        return sivm_box

    def create_sivm_controls(self):
        """ """
        layout = QVBoxLayout()

        row1 = QHBoxLayout()
        # self.reduced_dataset = CheckBox(text="Apply to reduced dataset")
        self.masked_dataset = CheckBox(text="Apply to masked dataset")
        self.modes_combobox = ComboBox(
            choices=self.data.modes, label="Select the imaging mode"
        )
        row1.addWidget(self.masked_dataset.native)
        row1.addWidget(self.modes_combobox.native)
        layout.addLayout(row1)

        # row2 = QHBoxLayout()
        # row2.addWidget(self.masked_dataset.native)
        # layout.addLayout(row2)

        self.n_endmembers_spinbox = SpinBox(
            min=1, max=500, value=10, step=1, name="Endmembers"
        )

        layout.addWidget(Container(widgets=[self.n_endmembers_spinbox]).native)

        row2 = QHBoxLayout()
        self.modes_vertex_analysis = ComboBox(
            choices=["SiVM", "VCA", "N-FINDR"],
            label="Select the vertex analysis mode",
        )
        run_btn = PushButton(text="Run endmember analysis")
        run_btn.clicked.connect(self.run_endmember_analysis)
        row2.addWidget(
            Container(widgets=[self.modes_vertex_analysis, run_btn]).native
        )
        layout.addLayout(row2)

        return layout

    def create_sivm_analysis(self):
        """ """
        layout = QVBoxLayout()
        row1 = QHBoxLayout()
        self.sivm_basis_multiselecton = Select(
            label="Select Bases", choices=[]
        )
        self.sivm_basis_multiselecton.changed.connect(
            self.on_basis_selection_changed
        )

        # select_bases_btn = PushButton(text="Select bases")
        # select_bases_btn.clicked.connect(self.plot_mean_spectrum)

        row1.addWidget(self.sivm_basis_multiselecton.native)
        layout.addLayout(row1)
        return layout

    def create_spectrum_area(self):
        """ """
        layout = QVBoxLayout()
        self.mean_plot = FigureCanvas(Figure(figsize=(5, 3)))
        self.mean_plot.setMinimumSize(300, 450)
        self.mean_plot_toolbar = NavigationToolbar(self.mean_plot, self)
        self.plot_widget.customize_toolbar(self.mean_plot_toolbar)
        self.plot_widget.setup_plot(self.mean_plot)

        # mean_btn = PushButton(text="Mean Spectrum")
        # self.std_checkbox = CheckBox(text="Plot Std Dev")
        # self.norm_checkbox = CheckBox(text="Normalize")
        # self.derivative_checkbox = CheckBox(text="Derivative")

        # mean_btn.clicked.connect(self.plot_mean_spectrum)

        # controls = [
        #    self.std_checkbox,
        #    self.norm_checkbox,
        #    self.derivative_checkbox,
        #    mean_btn,
        # ]
        # layout.addWidget(Container(widgets=controls).native)
        layout.addWidget(self.mean_plot)
        layout.addWidget(self.mean_plot_toolbar)

        # Export button
        export_btn = PushButton(text="Export spectra as .txt")
        export_btn.clicked.connect(self.export_spectrum)
        layout.addWidget(Container(widgets=[export_btn]).native)
        return layout

    def create_nnls(self):
        """ """
        layout = QVBoxLayout()

        run_btn = PushButton(text="Run NNLS")
        run_btn.clicked.connect(self.run_nnls)
        layout.addWidget(run_btn.native)

        self.angle_spinbox = FloatSpinBox(
            min=0.0, max=1.0, value=0.1, step=0.1, name="Cosine"
        )
        run_sam_btn = PushButton(text="Run SAM")
        run_sam_btn.clicked.connect(self.run_sam)
        layout.addWidget(
            Container(widgets=[self.angle_spinbox, run_sam_btn]).native
        )

        return layout

    def run_endmember_analysis(self):
        """Perform SiVM"""
        self.sivm_basis_multiselecton.value = []
        mode = self.modes_combobox.value
        analysis_mode = self.modes_vertex_analysis.value
        n_basis = self.n_endmembers_spinbox.value
        options = [f"Basis {i}" for i in range(n_basis)]

        if self.masked_dataset.value:
            dataset = self.data.hypercubes_masked[mode]
            # data_reshaped = dataset.reshape(
            #    dataset.shape[0] * dataset.shape[1], -1
            # )
            dataset = np.nan_to_num(dataset, nan=0)

            # self.points = np.array(
            #    np.where(~np.isnan(np.mean(data_reshaped, axis=1)))
            # ).flatten()

        # elif self.reduced_dataset.value:
        #    dataset = self.data.hypercubes_red[mode]
        #    self.points = []
        else:
            dataset = self.data.hypercubes[mode]
            self.points = []

        self.data.vertex_analysis(
            dataset,
            mode,
            n_basis,
            analysis_mode,
        )

        self.sivm_basis_multiselecton.choices = options
        show_info("Endmember analysis completed!")

    def on_basis_selection_changed(self, value):
        mode = self.modes_combobox.value

        print("Selected bases:", value)
        print(self.data.vertex_basis[mode].shape)
        print(type(value))
        print(len(value))
        # print("Selected:", int(value[:,6:]))

        self.basis_numbers = [int(s.split()[1]) for s in value]
        self.selected_basis = self.data.vertex_basis[mode][
            :, self.basis_numbers
        ]
        print(self.selected_basis.shape)
        selected_basis_print = self.selected_basis

        if mode == "Fused":
            fusion_point = self.data.wls[self.data.fusion_modes[0]].shape[0]
            data1 = self.data.hypercubes[self.data.fusion_modes[0]]
            print(data1.shape)
            data2 = self.data.hypercubes[self.data.fusion_modes[1]]
            data1_reshaped = data1.reshape(-1, data1.shape[2])
            print(data1_reshaped.shape)
            data2_reshaped = data2.reshape(-1, data2.shape[2])
            print(self.data.fusion_norm)
            # xxx aggiustare corrections

            if self.data.fusion_norm == "l2":
                print("Correcting for l2")
                corr1 = np.linalg.norm(data1_reshaped, ord=None)
                print(corr1)
                corr2 = np.linalg.norm(data2_reshaped, ord=None)
                selected_basis_print[:fusion_point, :] = (
                    selected_basis_print[:fusion_point, :] * corr1
                )
                selected_basis_print[fusion_point:, :] = (
                    selected_basis_print[fusion_point:, :] * corr2
                )

            if self.data.fusion_norm == "std":
                print("Correcting for std")
                print(np.std(data1_reshaped).shape)
                print(np.mean(data1_reshaped).shape)
                selected_basis_print[:fusion_point, :] = selected_basis_print[
                    :fusion_point, :
                ] * np.std(data1_reshaped) + np.mean(data1_reshaped)
                selected_basis_print[fusion_point:, :] = selected_basis_print[
                    fusion_point:, :
                ] * np.std(data2_reshaped) + np.mean(data2_reshaped)

            if self.data.fusion_norm == "Frobenius norm":
                selected_basis_print[:fusion_point, :] = selected_basis_print[
                    :fusion_point, :
                ] * np.linalg.norm(data1_reshaped, ord=None)
                selected_basis_print[fusion_point:, :] = selected_basis_print[
                    fusion_point:, :
                ] * np.linalg.norm(data2_reshaped, ord=None)

            if self.data.fusion_norm == "Z score":
                print("Correcting for Z score")
                mu1, sigma1 = np.mean(data1_reshaped), np.std(data1_reshaped)
                mu2, sigma2 = np.mean(data2_reshaped), np.std(data2_reshaped)
                selected_basis_print[:fusion_point, :] = (
                    selected_basis_print[:fusion_point, :] * sigma1 + mu1
                )
                selected_basis_print[fusion_point:, :] = (
                    selected_basis_print[fusion_point:, :] * sigma2 + mu2
                )

            if self.data.fusion_norm == "Z score - spectrum":
                mu1, sigma1 = data1.mean(axis=(0, 1)), data1.std(axis=(0, 1))
                mu2, sigma2 = data2.mean(axis=(0, 1)), data2.std(axis=(0, 1))
                print(mu2.shape, sigma2.shape)
                sigma1[sigma1 == 0] = 1
                sigma2[sigma2 == 0] = 1
                selected_basis_print[:fusion_point, :] = (
                    selected_basis_print[:fusion_point, :] * sigma1[..., None]
                    + mu1[..., None]
                )
                selected_basis_print[fusion_point:, :] = (
                    selected_basis_print[fusion_point:, :] * sigma2[..., None]
                    + mu2[..., None]
                )

        self.plot_widget.show_spectra(
            self.mean_plot,
            selected_basis_print,
            mode,
            basis_numbers=self.basis_numbers,
            export_txt_flag=False,
        )

        show_info(f"SiVM bases selected: {self.basis_numbers}")

    def export_spectrum(self):
        """Export the mean spectrum"""
        mode = self.modes_combobox.value

        self.plot_widget.show_spectra(
            self.mean_plot,
            self.selected_basis,
            mode,
            basis_numbers=self.basis_numbers,
            export_txt_flag=True,
        )

    def run_nnls(self):
        """Perform NNLS"""
        mode = self.modes_combobox.value

        if self.masked_dataset.value:
            dataset = self.data.hypercubes_masked[mode]
            data_reshaped = dataset.reshape(
                dataset.shape[0] * dataset.shape[1], -1
            )
            self.points = np.array(
                np.where(~np.isnan(np.mean(data_reshaped, axis=1)))
            ).flatten()

            dataset = np.nan_to_num(dataset, nan=0)

        # elif self.reduced_dataset.value:
        #    dataset = self.data.hypercubes_red[mode]
        #    self.points = []
        else:
            dataset = self.data.hypercubes[mode]
            self.points = []

        self.data.nnls_analysis(
            dataset,
            mode,
            W=self.selected_basis,
        )
        self.viewer.add_image(
            self.data.nnls_maps[mode].transpose(2, 0, 1),
            name=str(mode) + " - NNLS",
            # ={"type": "hyperspectral_cube"},
        )

    def run_sam(self):
        """Perform NNLS"""
        mode = self.modes_combobox.value

        if self.masked_dataset.value:
            dataset = self.data.hypercubes_masked[mode]
            data_reshaped = dataset.reshape(
                dataset.shape[0] * dataset.shape[1], -1
            )
            self.points = np.array(
                np.where(~np.isnan(np.mean(data_reshaped, axis=1)))
            ).flatten()

            dataset = np.nan_to_num(dataset, nan=0)

        # elif self.reduced_dataset.value:
        #    dataset = self.data.hypercubes_red[mode]
        #    self.points = []
        else:
            dataset = self.data.hypercubes[mode]
            self.points = []

        self.data.sam_analysis(
            dataset,
            mode,
            W=self.selected_basis,
            angle=self.angle_spinbox.value,
        )
        self.viewer.add_image(
            self.data.sam_maps[mode].transpose(2, 0, 1),
            name=str(mode)
            + " - SAM with angle "
            + str(self.angle_spinbox.value),
            colormap="gray_r",
            # ={"type": "hyperspectral_cube"},
        )
