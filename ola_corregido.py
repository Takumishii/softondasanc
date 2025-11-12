
import sys
import numpy as np
import pyqtgraph as pg
import sounddevice as sd
from PyQt5.QtWidgets import (QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel,
                             QHBoxLayout, QPushButton, QLineEdit, QGridLayout)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import math

class MatplotlibPlot(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 2))
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(-2.5, 2.5)
        self.punto, = self.ax.plot([], [], 'wo', markersize=8)
        self.ax.set_facecolor("black")
        self.ax.set_title("Partícula en Onda Estacionaria", color='white')
        self.ax.tick_params(colors='white')
        self.ax.yaxis.label.set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.fig.tight_layout()

    def update_point(self, y):
        self.punto.set_data([5], [y])
        self.draw()

class SimuladorOndas(QWidget):
    def __init__(self):
        super().__init__()
        self.t = 0
        self.modo = "super"
        self.forzar_destruccion = False
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar)
        self.timer.start(30)

    def initUI(self):
        layout = QVBoxLayout()
        self.param_layout = QGridLayout()

        self.E0 = 1.0
        self.k = 2 * np.pi
        self.w = 3.0
        self.phi = 0
        self.E1 = 1.0
        self.k1 = 2 * np.pi
        self.w1 = 3.0
        self.phi1 = math.pi

        self.inputs = {}
        labels = ["E0", "k", "w", "phi", "E1", "k1", "w1", "phi1"]
        valores = [self.E0, self.k / np.pi, self.w, self.phi,
                   self.E1, self.k1 / np.pi, self.w1, self.phi1]

        for i, (label, val) in enumerate(zip(labels, valores)):
            self.param_layout.addWidget(QLabel(label), i, 0)
            entry = QLineEdit(str(val))
            self.inputs[label] = entry
            self.param_layout.addWidget(entry, i, 1)

        self.update_params()

        self.btn_simple = QPushButton("Onda Simple")
        self.btn_super = QPushButton("Superposición")
        self.btn_est = QPushButton("Estacionaria")
        self.btn_destructiva = QPushButton("Interferencia Destructiva Total")

        self.btn_simple.clicked.connect(lambda: self.setModo("simple"))
        self.btn_super.clicked.connect(lambda: self.setModo("super"))
        self.btn_est.clicked.connect(lambda: self.setModo("est"))
        self.btn_destructiva.clicked.connect(self.set_interferencia_destruccion)

        self.control_layout = QHBoxLayout()
        for btn in [self.btn_simple, self.btn_super, self.btn_est, self.btn_destructiva]:
            self.control_layout.addWidget(btn)

        self.plot1 = pg.PlotWidget(title="Onda 1")
        self.plot2 = pg.PlotWidget(title="Onda 2")
        self.plot3 = pg.PlotWidget(title="Resultado")

        self.curve1 = self.plot1.plot(pen='b')
        self.curve2 = self.plot2.plot(pen='r')
        self.curve3 = self.plot3.plot(pen='g')

        self.matplot = MatplotlibPlot()

        self.x = np.linspace(0, 4 * np.pi, 500)

        layout.addLayout(self.param_layout)
        layout.addLayout(self.control_layout)
        layout.addWidget(self.plot1)
        layout.addWidget(self.plot2)
        layout.addWidget(self.plot3)
        layout.addWidget(self.matplot)
        self.setLayout(layout)
        self.setModo("super")

    def setModo(self, modo):
        self.update_params()
        self.modo = modo
        self.forzar_destruccion = False
        self.t = 0
        self.plot2.setVisible(modo == "super")
        self.plot3.setVisible(modo == "super")
        self.matplot.setVisible(modo == "est")

    def update_params(self):
        try:
            self.E0 = float(self.inputs["E0"].text())
            self.k = float(self.inputs["k"].text()) * np.pi
            self.w = float(self.inputs["w"].text())
            self.phi = float(self.inputs["phi"].text())
            self.E1 = float(self.inputs["E1"].text())
            self.k1 = float(self.inputs["k1"].text()) * np.pi
            self.w1 = float(self.inputs["w1"].text())
            self.phi1 = float(self.inputs["phi1"].text())
        except:
            pass

    def set_interferencia_destruccion(self):
        self.inputs["E1"].setText(self.inputs["E0"].text())
        self.inputs["k1"].setText(self.inputs["k"].text())
        self.inputs["w1"].setText(self.inputs["w"].text())
        phi_orig = float(self.inputs["phi"].text())
        self.inputs["phi1"].setText(str(phi_orig + math.pi))
        self.setModo("super")
        self.forzar_destruccion = True

    def actualizar(self):
        self.update_params()
        t = self.t
        x = self.x
        y1 = self.E0 * np.sin(self.k * x - self.w * t + self.phi)

        if self.forzar_destruccion:
            y2 = -y1
        else:
            y2 = self.E1 * np.sin(self.k1 * x - self.w1 * t + self.phi1)

        if self.modo == "simple":
            self.curve1.setData(x, y1)
            self.curve2.clear()
            self.curve3.clear()

        elif self.modo == "super":
            y_total = y1 + y2
            self.curve1.setData(x, y1)
            self.curve2.setData(x, y2)
            self.curve3.setData(x, y_total)

        elif self.modo == "est":
            y_est = 2 * self.E0 * np.cos(self.k * x) * np.sin(self.w * t)
            self.curve1.setData(x, y_est)
            self.curve2.clear()
            self.curve3.clear()
            y_p = 2 * self.E0 * np.cos(self.k * 2*np.pi) * np.sin(self.w * t)
            self.matplot.update_point(y_p)

        self.t += 0.1
