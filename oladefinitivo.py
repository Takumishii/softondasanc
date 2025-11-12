# Requiere: pip install PyQt5 pyqtgraph sounddevice matplotlib numpy

import sys
import numpy as np
import sounddevice as sd
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QPushButton, QLineEdit, QGridLayout, QGroupBox,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QScrollArea, QGroupBox


# =======================
# Gráfico Matplotlib para Superposición
# =======================
class SuperposicionMatplotlib(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(8, 6))
        super().__init__(self.fig)
        self.ax1 = self.fig.add_subplot(311)
        self.ax2 = self.fig.add_subplot(312, sharex=self.ax1)
        self.ax3 = self.fig.add_subplot(313, sharex=self.ax1)

        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_xlim(0, 4 * np.pi)
            ax.set_ylim(-3, 3)
            ax.grid(True)

        self.line1, = self.ax1.plot([], [], 'b', label='Onda 1')
        self.line2, = self.ax2.plot([], [], 'r', label='Onda 2')
        self.line_sum, = self.ax3.plot([], [], 'g', label='Suma')

        self.ax3.set_xlabel("x (posición)")
        self.ax1.legend(); self.ax2.legend(); self.ax3.legend()

    def update_plot(self, x, y1, y2):
        self.line1.set_data(x, y1)
        self.line2.set_data(x, y2)
        self.line_sum.set_data(x, y1 + y2)
        self.draw()

# =======================
# Gráfico Matplotlib para Estacionaria (traza partícula)
# =======================
class EstacionariaMatplotlib(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 2))
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(-2.5, 2.5)
        self.punto, = self.ax.plot([], [], 'ro', markersize=8)
        self.traza, = self.ax.plot([], [], 'b-', alpha=0.5)
        self.ax.grid()
        self.fig.tight_layout()
        self.t_data = []
        self.y_data = []

    def reset(self):
        self.t_data.clear()
        self.y_data.clear()
        self.punto.set_data([], [])
        self.traza.set_data([], [])
        self.ax.set_xlim(0, 10)
        self.draw()

    def update_plot(self, t, y):
        self.t_data.append(t)
        self.y_data.append(y)
        self.punto.set_data([t], [y])
        self.traza.set_data(self.t_data, self.y_data)
        self.ax.set_xlim(max(0, t - 5), t + 1)
        self.draw()

# =======================
# Simulador de Ondas
# =======================
class SimuladorOndas(QWidget):
    def __init__(self):
        super().__init__()
        self.t = 0
        self.modo = "simple"
        self.x = np.linspace(0, 4 * np.pi, 500)
        self.px = 2 * np.pi  # Posición de la partícula

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar)
        self.timer.start(30)

    def initUI(self):

        layout = QVBoxLayout()

        # =====================
        # Grupo de Parámetros en scroll
        # =====================
        group_box = QGroupBox("Parámetros de la Onda")
        self.param_layout = QGridLayout()

        self.E0 = 2.0
        self.k = np.pi
        self.w = 5.0
        self.phi = 0.5
        self.E1 = 1.5
        self.k1 = 1.5 * np.pi
        self.w1 = 4.0
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

        group_box.setLayout(self.param_layout)

        scroll = QScrollArea()
        scroll.setWidget(group_box)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(180)

        layout.addWidget(scroll)

        # =====================
        # Botones
        # =====================
        self.btn_simple = QPushButton("Onda Simple")
        self.btn_super = QPushButton("Superposición")
        self.btn_est = QPushButton("Estacionaria")
        self.btn_destructiva = QPushButton("Ejemplo Interferencia Destructiva Total")

        self.btn_simple.clicked.connect(lambda: self.setModo("simple"))
        self.btn_super.clicked.connect(lambda: self.setModo("super"))
        self.btn_est.clicked.connect(lambda: self.setModo("est"))
        self.btn_destructiva.clicked.connect(self.set_interferencia_destr)

        self.control_layout = QHBoxLayout()
        for btn in [self.btn_simple, self.btn_super, self.btn_est, self.btn_destructiva]:
            self.control_layout.addWidget(btn)

        layout.addLayout(self.control_layout)

        # =====================
        # Gráficos
        # =====================
        self.plot_simple = pg.PlotWidget(title="Onda Simple")
        self.curve_simple = self.plot_simple.plot(pen='b')

        self.mpl_super = SuperposicionMatplotlib()
        self.mpl_est = EstacionariaMatplotlib()
        self.plot_est = pg.PlotWidget(title="Onda Estacionaria")
        self.curve_est = self.plot_est.plot(pen='g')

        layout.addWidget(self.plot_simple)
        layout.addWidget(self.mpl_super)

        estacionaria_layout = QHBoxLayout()
        estacionaria_layout.addWidget(self.plot_est, 1)
        estacionaria_layout.addWidget(self.mpl_est, 2)
        layout.addLayout(estacionaria_layout)

        self.setLayout(layout)
        self.setModo("super")

    def setModo(self, modo):
        self.update_params()
        self.modo = modo
        self.t = 0
        self.mpl_est.reset()
        self.plot_simple.setVisible(modo == "simple")
        self.mpl_super.setVisible(modo == "super")
        self.plot_est.setVisible(modo == "est")
        self.mpl_est.setVisible(modo == "est")

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

    def set_interferencia_destr(self):
        self.inputs["E1"].setText(self.inputs["E0"].text())
        self.inputs["k1"].setText(self.inputs["k"].text())
        self.inputs["w1"].setText(self.inputs["w"].text())
        phi_orig = float(self.inputs["phi"].text())
        self.inputs["phi1"].setText(str(phi_orig + math.pi))
        self.setModo("super")

    def actualizar(self):
        self.update_params()
        t = self.t
        x = self.x

        if self.modo == "simple":
            y1 = self.E0 * np.sin(self.k * x - self.w * t + self.phi)
            self.curve_simple.setData(x, y1)
            self.t += 0.1

        elif self.modo == "super":
            y1 = self.E0 * np.sin(self.k * x - self.w * t + self.phi)
            y2 = self.E1 * np.sin(self.k1 * x - self.w1 * t + self.phi1)
            self.mpl_super.update_plot(x, y1, y2)
            self.t += 0.1

        elif self.modo == "est":
            y_est = 2 * self.E0 * np.cos(self.k * x) * np.sin(self.w * t)
            y_particula = 2 * self.E0 * np.cos(self.k * self.px) * np.sin(self.w * t)
            self.curve_est.setData(x, y_est)
            self.mpl_est.update_plot(t, y_particula)
            self.t += 0.1

# =======================
# Audio y Calculadora (sin cambios)
# =======================

class VisualAudio(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.plot_orig = pg.PlotWidget(title="Audio Original")
        self.curve_orig = self.plot_orig.plot(pen='y')
        self.plot_inv = pg.PlotWidget(title="Audio Invertido")
        self.curve_inv = self.plot_inv.plot(pen='c')
        self.plot_sum = pg.PlotWidget(title="Resultado Cancelado")
        self.curve_sum = self.plot_sum.plot(pen='m')
        self.btn_toggle = QPushButton("Activar Microfono Cancelación de audio")
        self.btn_toggle.clicked.connect(self.toggle_stream)
        layout.addWidget(self.plot_orig)
        layout.addWidget(self.plot_inv)
        layout.addWidget(self.plot_sum)
        layout.addWidget(self.btn_toggle)
        self.setLayout(layout)
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

    def toggle_stream(self):
        if self.running:
            self.stream.stop(); self.stream.close()
            self.running = False
            self.timer.stop()
            self.btn_toggle.setText("Activar")
        else:
            self.audio_in = np.zeros(1024)
            self.audio_inv = np.zeros(1024)
            self.audio_sum = np.zeros(1024)
            self.stream = sd.Stream(channels=1, callback=self.callback, samplerate=44100, blocksize=1024)
            self.stream.start()
            self.running = True
            self.timer.start(30)
            self.btn_toggle.setText("Desactivar")

    def callback(self, indata, outdata, frames, time, status):
        self.audio_in = indata[:, 0]
        self.audio_inv = -self.audio_in
        self.audio_sum = self.audio_in + self.audio_inv
        outdata[:, 0] = self.audio_inv

    def update_plot(self):
        self.curve_orig.setData(self.audio_in)
        self.curve_inv.setData(self.audio_inv)
        self.curve_sum.setData(self.audio_sum)

class CalculadoraOndas(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()

        self.inputs = {}
        campos = ["Frecuencia (f)", "Longitud de onda (λ)", "Velocidad (v)", "Número de onda (k)", "Pulsación angular (ω)"]
        for i, campo in enumerate(campos):
            layout.addWidget(QLabel(campo + ":"), i, 0)
            self.inputs[campo] = QLineEdit()
            layout.addWidget(self.inputs[campo], i, 1)

        self.resultado = QLabel("Resultado: ...")
        btn = QPushButton("Calcular valores restantes")
        btn.clicked.connect(self.calcular)

        layout.addWidget(btn, len(campos), 0, 1, 2)
        layout.addWidget(self.resultado, len(campos) + 1, 0, 1, 2)

        self.setLayout(layout)

    def calcular(self):
        try:
            vals = {}
            for campo, entrada in self.inputs.items():
                texto = entrada.text().strip()
                if texto != "":
                    vals[campo] = float(texto)

            # Relaciones entre parámetros:
            # v = f * λ
            # k = 2π / λ
            # ω = 2π * f

            if "Frecuencia (f)" in vals and "Longitud de onda (λ)" in vals:
                vals["Velocidad (v)"] = vals["Frecuencia (f)"] * vals["Longitud de onda (λ)"]
            if "Velocidad (v)" in vals and "Frecuencia (f)" in vals and "Longitud de onda (λ)" not in vals:
                vals["Longitud de onda (λ)"] = vals["Velocidad (v)"] / vals["Frecuencia (f)"]
            if "Velocidad (v)" in vals and "Longitud de onda (λ)" in vals and "Frecuencia (f)" not in vals:
                vals["Frecuencia (f)"] = vals["Velocidad (v)"] / vals["Longitud de onda (λ)"]

            if "Longitud de onda (λ)" in vals:
                vals["Número de onda (k)"] = 2 * np.pi / vals["Longitud de onda (λ)"]
            if "Frecuencia (f)" in vals:
                vals["Pulsación angular (ω)"] = 2 * np.pi * vals["Frecuencia (f)"]

            # Mostrar resultados
            texto = "\n".join([f"{clave}: {valor:.3f}" for clave, valor in vals.items()])
            self.resultado.setText("Resultado:\n" + texto)
        except:
            self.resultado.setText("Error en los datos")


# =======================
# Ventana Principal
# =======================
class VentanaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador Completo de Ondas")
        self.resize(1000, 800)

        self.stacked_layout = QVBoxLayout()
        self.setLayout(self.stacked_layout)

        self.menu_widget = self.crear_menu_inicial()
        self.stacked_layout.addWidget(self.menu_widget)

        self.tabs_widget = self.crear_tabs()
        self.tabs_widget.hide()
        self.stacked_layout.addWidget(self.tabs_widget)

        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid #aaa;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                font-size: 16px;
                border-radius: 8px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLabel {
                font-weight: bold;
                font-size: 24px;
                margin-bottom: 20px;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTabBar::tab {
                padding: 8px;
                background: #ddd;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #f5f5f5;
                font-weight: bold;
            }
        """)

    def crear_menu_inicial(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        titulo = QLabel("🌊 Simulador Interactivo de Cancelación Activa de Ruido mediante Interferencia Destructiva")
        titulo.setAlignment(Qt.AlignCenter)

        btn_simulador = QPushButton("Iniciar Simulador de Ondas")
        btn_simulador.clicked.connect(lambda: self.mostrar_tabs(0))

        btn_calculadora = QPushButton("Abrir Calculadora de Ondas")
        btn_calculadora.clicked.connect(lambda: self.mostrar_tabs(1))

        btn_audio = QPushButton("Visualizar Audio en Tiempo Real")
        btn_audio.clicked.connect(lambda: self.mostrar_tabs(2))

        layout.addWidget(titulo)
        layout.addSpacing(20)
        layout.addWidget(btn_simulador)
        layout.addWidget(btn_calculadora)
        layout.addWidget(btn_audio)

        widget.setLayout(layout)
        return widget

    def crear_tabs(self):
        tabs = QTabWidget()

        self.simulador = SimuladorOndas()
        self.calculadora = CalculadoraOndas()
        self.audio = VisualAudio()

        tabs.addTab(self.simulador, "🌊 Simulador de Ondas")
        tabs.addTab(self.calculadora, "📊 Calculadora")
        tabs.addTab(self.audio, "🎧 Audio en Tiempo Real")

        return tabs

    def mostrar_tabs(self, index):
        self.menu_widget.hide()
        self.tabs_widget.show()
        self.tabs_widget.setCurrentIndex(index)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec_())