"""
Just Dance Mashup Creator
Единый файл с поддержкой русского и английского языков.
/ Single-file tool with Russian and English language support.

Зависимости / Dependencies:
    pip install PyQt6 opencv-python pydub numpy
    Требуется FFmpeg в PATH (для pydub).
    FFmpeg is required in PATH (for pydub).
"""

import sys
import cv2
import numpy as np
from pydub import AudioSegment

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QFileDialog, QColorDialog, QSpinBox,
    QGraphicsView, QGraphicsScene, QGraphicsPathItem,
    QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor,
    QPainterPath, QBrush
)


# =====================================================================
#  ЛОКАЛИЗАЦИЯ / LOCALIZATION
# =====================================================================

TRANSLATIONS = {
    "ru": {
        "window_title":       "Just Dance Mashup Creator",
        "tab_video":          "Видео",
        "tab_audio":          "Аудио",
        "tab_pictograms":     "Пиктограммы",

        # Video
        "video_not_loaded":   "Видео не загружено",
        "load_video":         "Загрузить видео",
        "load_background":    "Загрузить фон",
        "pick_chroma_color":  "Выбрать цвет хромакея",
        "play":               "▶ Воспроизвести",
        "pause":              "⏸ Пауза",
        "chroma_threshold":   "Порог хромакея:",
        "open_video":         "Открыть видео",
        "filter_video":       "Видео (*.mp4 *.webm *.avi *.mov)",
        "open_background":    "Открыть фон",
        "filter_images":      "Изображения (*.png *.jpg *.jpeg)",
        "pick_color_title":   "Выбор цвета хромакея",

        # Audio
        "audio_not_loaded":   "Аудио не загружено",
        "load_audio":         "Загрузить аудио",
        "export_audio":       "Экспортировать",
        "open_audio":         "Открыть аудио",
        "filter_audio":       "Аудио (*.wav *.mp3 *.ogg)",
        "save_audio":         "Сохранить аудио",
        "filter_audio_save":  "WAV (*.wav);;MP3 (*.mp3);;OGG (*.ogg)",
        "audio_info":         "{path} | {dur:.1f} сек | {ch} канал(ов)",

        # Pictograms
        "color":              "Цвет",
        "thickness":          "Толщина:",
        "clear":              "Очистить",
        "import_pictogram":   "Импорт пиктограммы",
        "export_png":         "Экспорт PNG",
        "open_pictogram":     "Импорт пиктограммы",
        "filter_pictogram":   "Изображения (*.png *.jpg *.tga)",
        "save_pictogram":     "Сохранить пиктограмму",
        "filter_png":         "PNG (*.png)",

        # Language
        "language":           "Язык:",
    },
    "en": {
        "window_title":       "Just Dance Mashup Creator",
        "tab_video":          "Video",
        "tab_audio":          "Audio",
        "tab_pictograms":     "Pictograms",

        # Video
        "video_not_loaded":   "No video loaded",
        "load_video":         "Load video",
        "load_background":    "Load background",
        "pick_chroma_color":  "Pick chroma key color",
        "play":               "▶ Play",
        "pause":              "⏸ Pause",
        "chroma_threshold":   "Chroma threshold:",
        "open_video":         "Open video",
        "filter_video":       "Video (*.mp4 *.webm *.avi *.mov)",
        "open_background":    "Open background",
        "filter_images":      "Images (*.png *.jpg *.jpeg)",
        "pick_color_title":   "Choose chroma key color",

        # Audio
        "audio_not_loaded":   "No audio loaded",
        "load_audio":         "Load audio",
        "export_audio":       "Export",
        "open_audio":         "Open audio",
        "filter_audio":       "Audio (*.wav *.mp3 *.ogg)",
        "save_audio":         "Save audio",
        "filter_audio_save":  "WAV (*.wav);;MP3 (*.mp3);;OGG (*.ogg)",
        "audio_info":         "{path} | {dur:.1f} s | {ch} channel(s)",

        # Pictograms
        "color":              "Color",
        "thickness":          "Thickness:",
        "clear":              "Clear",
        "import_pictogram":   "Import pictogram",
        "export_png":         "Export PNG",
        "open_pictogram":     "Import pictogram",
        "filter_pictogram":   "Images (*.png *.jpg *.tga)",
        "save_pictogram":     "Save pictogram",
        "filter_png":         "PNG (*.png)",

        # Language
        "language":           "Language:",
    },
}


class Lang:
    """Простой глобальный объект локализации / Simple global i18n helper."""
    current = "ru"

    @classmethod
    def set(cls, code):
        if code in TRANSLATIONS:
            cls.current = code

    @classmethod
    def t(cls, key):
        return TRANSLATIONS[cls.current].get(key, key)


def tr(key):
    return Lang.t(key)


# =====================================================================
#  ВИДЕОРЕДАКТОР С ХРОМАКЕЕМ / VIDEO EDITOR WITH CHROMA KEY
# =====================================================================

class VideoEditorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.chroma_color = (0, 255, 0)   # BGR: зелёный / green
        self.threshold = 60
        self.background = None
        self.is_playing = False
        self._build_ui()
        self.retranslate()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 450)
        self.video_label.setStyleSheet("background: #1e1e1e; color: #aaa;")
        layout.addWidget(self.video_label)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton()
        self.btn_load.clicked.connect(self.load_video)

        self.btn_bg = QPushButton()
        self.btn_bg.clicked.connect(self.load_background)

        self.btn_pick_color = QPushButton()
        self.btn_pick_color.clicked.connect(self.pick_chroma_color)

        self.btn_play = QPushButton()
        self.btn_play.clicked.connect(self.toggle_play)

        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_bg)
        btn_layout.addWidget(self.btn_pick_color)
        btn_layout.addWidget(self.btn_play)
        layout.addLayout(btn_layout)

        self.lbl_threshold = QLabel()
        layout.addWidget(self.lbl_threshold)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(10, 150)
        self.slider.setValue(self.threshold)
        self.slider.valueChanged.connect(self._on_threshold)
        layout.addWidget(self.slider)

    def retranslate(self):
        self.video_label.setText(tr("video_not_loaded"))
        self.btn_load.setText(tr("load_video"))
        self.btn_bg.setText(tr("load_background"))
        self.btn_pick_color.setText(tr("pick_chroma_color"))
        self.btn_play.setText(tr("pause") if self.is_playing else tr("play"))
        self.lbl_threshold.setText(tr("chroma_threshold"))

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("open_video"), "", tr("filter_video")
        )
        if path:
            if self.cap:
                self.cap.release()
            self.cap = cv2.VideoCapture(path)
            self.timer.start(33)

    def load_background(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("open_background"), "", tr("filter_images")
        )
        if path:
            self.background = cv2.imread(path)

    def pick_chroma_color(self):
        color = QColorDialog.getColor(
            title=tr("pick_color_title")
        )
        if color.isValid():
            self.chroma_color = (
                color.blue(), color.green(), color.red()
            )

    def _on_threshold(self, value):
        self.threshold = value

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.is_playing = False
            self.btn_play.setText(tr("play"))
        else:
            self.timer.start(33)
            self.is_playing = True
            self.btn_play.setText(tr("pause"))

    def next_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        result = self._apply_chroma_key(frame)

        rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w,
                      QImage.Format.Format_RGB888)
        self.video_label.setPixmap(
            QPixmap.fromImage(qimg).scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def _apply_chroma_key(self, frame):
        diff = cv2.absdiff(
            frame, np.full_like(frame, self.chroma_color)
        )
        mask = np.all(diff < self.threshold, axis=2).astype(np.uint8) * 255
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        mask_inv = cv2.bitwise_not(mask)

        if self.background is not None:
            bg = cv2.resize(
                self.background, (frame.shape[1], frame.shape[0])
            )
        else:
            bg = np.zeros_like(frame)

        fg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        bg_part = cv2.bitwise_and(bg, bg, mask=mask)
        return cv2.add(fg, bg_part)


# =====================================================================
#  АУДИОРЕДАКТОР С ВОЛНОВОЙ ФОРМОЙ / AUDIO EDITOR WITH WAVEFORM
# =====================================================================

class WaveformView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.samples = None

    def set_audio(self, samples):
        self.samples = samples
        self.scene.clear()
        self._draw_waveform()

    def _draw_waveform(self):
        if self.samples is None or len(self.samples) == 0:
            return

        w = max(self.viewport().width(), 1)
        h = max(self.viewport().height(), 1)
        step = max(1, len(self.samples) // w)

        pen = QPen(QColor("#00d4ff"))
        pen.setWidth(1)

        prev_x, prev_y = 0, h // 2
        for i in range(0, len(self.samples), step):
            chunk = self.samples[i:i + step]
            if len(chunk) == 0:
                continue
            peak = float(np.max(np.abs(chunk)))
            x = int(i / len(self.samples) * w)
            y = int(h // 2 - peak * (h // 2) * 0.9)
            self.scene.addLine(prev_x, prev_y, x, y, pen)
            prev_x, prev_y = x, y


class AudioEditorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.audio = None
        self._build_ui()
        self.retranslate()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.waveform = WaveformView()
        self.waveform.setMinimumHeight(200)
        layout.addWidget(self.waveform)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton()
        self.btn_load.clicked.connect(self.load_audio)

        self.btn_export = QPushButton()
        self.btn_export.clicked.connect(self.export_audio)

        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

    def retranslate(self):
        self.btn_load.setText(tr("load_audio"))
        self.btn_export.setText(tr("export_audio"))
        if self.audio is None:
            self.info_label.setText(tr("audio_not_loaded"))
        else:
            # пересобрать строку информации / rebuild info line
            self._update_info(self.current_path)

    def _update_info(self, path):
        self.info_label.setText(tr("audio_info").format(
            path=path,
            dur=len(self.audio) / 1000,
            ch=self.audio.channels
        ))

    def load_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("open_audio"), "", tr("filter_audio")
        )
        if not path:
            return

        self.audio = AudioSegment.from_file(path)
        self.current_path = path

        samples = np.array(self.audio.get_array_of_samples())
        if self.audio.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)

        samples = samples.astype(np.float32)
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples /= max_val

        self.waveform.set_audio(samples)
        self._update_info(path)

    def export_audio(self):
        if not self.audio:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("save_audio"), "", tr("filter_audio_save")
        )
        if path:
            fmt = path.split(".")[-1]
            self.audio.export(path, format=fmt)


# =====================================================================
#  РЕДАКТОР И РИСОВАНИЕ ПИКТОГРАММ / PICTOGRAM EDITOR
# =====================================================================

class DrawingCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.drawing = False
        self.last_point = QPointF()
        self.current_path = None
        self.current_item = None
        self.pen_color = QColor("#000000")
        self.pen_width = 8

        self.scene.setSceneRect(0, 0, 600, 600)
        self.scene.setBackgroundBrush(QBrush(QColor("#ffffff")))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = self.mapToScene(event.pos())
            self.current_path = QPainterPath(self.last_point)
            self.current_item = QGraphicsPathItem()
            self.current_item.setPen(
                QPen(self.pen_color, self.pen_width,
                     Qt.PenStyle.SolidLine,
                     Qt.PenCapStyle.RoundCap,
                     Qt.PenJoinStyle.RoundJoin)
            )
            self.scene.addItem(self.current_item)

    def mouseMoveEvent(self, event):
        if self.drawing and self.current_path:
            point = self.mapToScene(event.pos())
            self.current_path.lineTo(point)
            self.current_item.setPath(self.current_path)
            self.last_point = point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.current_path = None

    def clear_canvas(self):
        self.scene.clear()
        self.scene.setBackgroundBrush(QBrush(QColor("#ffffff")))

    def export_png(self, path):
        rect = self.scene.sceneRect()
        image = QPixmap(int(rect.width()), int(rect.height()))
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()
        image.save(path, "PNG")


class PictogramEditorTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self.retranslate()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.canvas = DrawingCanvas()
        layout.addWidget(self.canvas, stretch=1)

        tools = QHBoxLayout()

        self.btn_color = QPushButton()
        self.btn_color.clicked.connect(self._pick_color)

        self.lbl_thickness = QLabel()
        self.btn_width = QSpinBox()
        self.btn_width.setRange(1, 40)
        self.btn_width.setValue(8)
        self.btn_width.valueChanged.connect(self._on_width)

        self.btn_clear = QPushButton()
        self.btn_clear.clicked.connect(self.canvas.clear_canvas)

        self.btn_import = QPushButton()
        self.btn_import.clicked.connect(self._import_pictogram)

        self.btn_export = QPushButton()
        self.btn_export.clicked.connect(self._export_png)

        tools.addWidget(self.btn_color)
        tools.addWidget(self.lbl_thickness)
        tools.addWidget(self.btn_width)
        tools.addWidget(self.btn_clear)
        tools.addWidget(self.btn_import)
        tools.addWidget(self.btn_export)
        layout.addLayout(tools)

    def retranslate(self):
        self.btn_color.setText(tr("color"))
        self.lbl_thickness.setText(tr("thickness"))
        self.btn_clear.setText(tr("clear"))
        self.btn_import.setText(tr("import_pictogram"))
        self.btn_export.setText(tr("export_png"))

    def _pick_color(self):
        color = QColorDialog.getColor(self.canvas.pen_color)
        if color.isValid():
            self.canvas.pen_color = color

    def _on_width(self, value):
        self.canvas.pen_width = value

    def _import_pictogram(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("open_pictogram"), "", tr("filter_pictogram")
        )
        if path:
            pixmap = QPixmap(path)
            self.canvas.scene.clear()
            self.canvas.scene.addPixmap(
                pixmap.scaled(600, 600,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("save_pictogram"), "", tr("filter_png")
        )
        if path:
            self.canvas.export_png(path)


# =====================================================================
#  ГЛАВНОЕ ОКНО / MAIN WINDOW
# =====================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1400, 900)
        self._build_ui()
        self.retranslate()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Панель выбора языка / Language selector
        top = QHBoxLayout()
        self.lbl_language = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Русский", "ru")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.setCurrentIndex(
            0 if Lang.current == "ru" else 1
        )
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)

        top.addStretch(1)
        top.addWidget(self.lbl_language)
        top.addWidget(self.lang_combo)
        root.addLayout(top)

        self.tabs = QTabWidget()
        self.video_tab = VideoEditorTab()
        self.audio_tab = AudioEditorTab()
        self.picto_tab = PictogramEditorTab()

        self.tabs.addTab(self.video_tab, "")
        self.tabs.addTab(self.audio_tab, "")
        self.tabs.addTab(self.picto_tab, "")

        root.addWidget(self.tabs, stretch=1)

    def _on_lang_changed(self, index):
        code = self.lang_combo.itemData(index)
        Lang.set(code)
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(tr("window_title"))
        self.lbl_language.setText(tr("language"))
        self.tabs.setTabText(0, tr("tab_video"))
        self.tabs.setTabText(1, tr("tab_audio"))
        self.tabs.setTabText(2, tr("tab_pictograms"))

        self.video_tab.retranslate()
        self.audio_tab.retranslate()
        self.picto_tab.retranslate()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())