from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from palmcue.settings import load_settings, save_settings
from palmcue.ui.runtime import Runtime
from palmcue.ui.theme import STYLE, app_icon
from palmcue.ui.widgets import GesturePreview, PracticeDeck, Preview, card, label


class MainWindow(QMainWindow):
    def __init__(self, settings_path: Path, camera=None):
        super().__init__()
        self.settings_path = settings_path
        self.settings, warning = load_settings(settings_path)
        self.setWindowTitle("PalmCue")
        self.setWindowIcon(app_icon())
        self.setStyleSheet(STYLE)
        self.resize(1120, 800)
        self.setMinimumSize(960, 650)
        root = QWidget()
        self.setCentralWidget(root)
        row = QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(190)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 28, 18, 22)
        side.addWidget(label("PalmCue", "brand"))
        side.addWidget(label("PRESENT WITH PRESENCE", "tagline"))
        side.addSpacing(35)
        self.nav = QButtonGroup(self)
        self.stack = QStackedWidget()
        for i, name in enumerate(("Practice", "Present", "Gesture guide", "Preferences", "Help")):
            button = QPushButton(name)
            button.setObjectName("nav")
            button.setCheckable(True)
            self.nav.addButton(button, i)
            side.addWidget(button)
        self.nav.idClicked.connect(self.navigate)
        self.nav.button(0).setChecked(True)
        side.addStretch()
        side.addWidget(label("A little movement.\nA clear message.", "tagline"))
        side.addSpacing(18)
        side.addWidget(label("PRIVATE BY DESIGN\nNo recording. No uploads.", "tagline"))
        row.addWidget(sidebar)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(26, 20, 26, 20)
        self.notice = label(warning, "notice")
        self.notice.setVisible(bool(warning))
        body_layout.addWidget(self.notice)
        body_layout.addWidget(self.stack)
        row.addWidget(body, 1)
        self.build_practice()
        self.build_present()
        self.build_guide()
        self.build_preferences()
        self.build_help()
        self.runtime = Runtime(self, camera)

    def page(self, eyebrow, title, subtitle):
        content = QWidget()
        content.setObjectName("page")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(2, 0, 10, 10)
        layout.setSpacing(16)
        layout.addWidget(label(eyebrow, "eyebrow"))
        layout.addWidget(label(title, "heading"))
        layout.addWidget(label(subtitle, "muted"))
        scroll = QScrollArea()
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        self.stack.addWidget(scroll)
        return layout

    def navigate(self, index):
        self.stack.setCurrentIndex(index)
        self.nav.button(index).setChecked(True)

    def build_practice(self):
        layout = self.page(
            "YOUR QUIET REHEARSAL SPACE",
            "Make yourself comfortable.",
            "Try a few gestures here. Your other apps stay untouched.",
        )
        self.welcome, box = card()
        self.welcome.setObjectName("banner")
        box.addWidget(label("Your first cue, in three small steps", "subheading"))
        box.addWidget(
            label(
                "1  Start your camera.\n2  Hold an open palm until the bar fills.\n"
                "3  Hold two fingers for next. Open your palm between commands."
            )
        )
        done = QPushButton("Got it")
        done.clicked.connect(self.dismiss_welcome)
        box.addWidget(done, alignment=Qt.AlignmentFlag.AlignLeft)
        self.welcome.setVisible(not self.settings.onboarding_done)
        layout.addWidget(self.welcome)
        row = QHBoxLayout()
        camera_card, camera_layout = card()
        top = QHBoxLayout()
        top.addWidget(label("Your space", "subheading"))
        top.addStretch()
        self.camera_badge = label("CAMERA OFF", "badge")
        top.addWidget(self.camera_badge)
        camera_layout.addLayout(top)
        self.preview = Preview()
        self.preview.area = self.settings.area
        camera_layout.addWidget(self.preview, 1)
        self.camera_status = label("Face a light and keep your whole hand in view.", "muted")
        camera_layout.addWidget(self.camera_status)
        self.camera_button = QPushButton("Start camera")
        self.camera_button.setObjectName("primary")
        camera_layout.addWidget(self.camera_button)
        row.addWidget(camera_card, 6)
        practice_card, practice_layout = card()
        practice_layout.addWidget(label("Try it here", "subheading"))
        self.deck = PracticeDeck()
        practice_layout.addWidget(self.deck, 1)
        self.gesture_status = label("Hold an open palm to unlock", "subheading")
        practice_layout.addWidget(self.gesture_status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Gesture hold progress")
        practice_layout.addWidget(self.progress)
        self.last_action = label("Waiting for your first cue", "muted")
        practice_layout.addWidget(self.last_action)
        self.lock_button = QPushButton("Lock controls")
        practice_layout.addWidget(self.lock_button)
        row.addWidget(practice_card, 5)
        layout.addLayout(row)
        layout.addWidget(
            label(
                "No calibration needed for most people. If a gesture feels "
                "difficult, try the guide or adjust your gesture area in Preferences.",
                "muted",
            )
        )
        layout.addStretch()

    def dismiss_welcome(self):
        self.welcome.hide()
        self.update_setting(onboarding_done=True)

    def build_present(self):
        layout = self.page(
            "WHEN YOU'RE READY",
            "Let your ideas take the stage.",
            "PalmCue works alongside your slides, quietly in the background.",
        )
        frame, box = card()
        box.addWidget(label("Choose your presentation", "subheading"))
        box.addWidget(
            label(
                "Open your slides in presentation mode first. Then select that "
                "window below. Refresh if you opened it just now.",
                "muted",
            )
        )
        self.targets = QComboBox()
        self.targets.setAccessibleName("Presentation window")
        self.targets.addItem("Open your presentation, then refresh", None)
        box.addWidget(self.targets)
        self.refresh_targets = QPushButton("Refresh windows")
        box.addWidget(self.refresh_targets, alignment=Qt.AlignmentFlag.AlignLeft)
        box.addWidget(
            label(
                "After Start, you have five seconds to bring that window to the "
                "front. Hold an open palm to unlock when you're ready."
            )
        )
        self.auto_present_check = QCheckBox(
            "Automatically start when a supported fullscreen slideshow appears"
        )
        self.auto_present_check.setChecked(self.settings.auto_present)
        self.auto_present_check.setToolTip(
            "Works with Canva and browser slides, PowerPoint, and common PDF viewers. "
            "PalmCue still waits five seconds and stays locked until you unlock it."
        )
        box.addWidget(self.auto_present_check)
        box.addWidget(
            label(
                "Automatic mode only recognizes fullscreen presentation apps. "
                "You can still choose a window yourself below.",
                "muted",
            )
        )
        self.present_button = QPushButton("Start presenting")
        self.present_button.setObjectName("primary")
        self.present_button.setEnabled(False)
        box.addWidget(self.present_button)
        self.session_status = label("Start the camera in Practice first.", "muted")
        box.addWidget(self.session_status)
        self.session_step = label("Step 1 · Start camera in Practice", "badge")
        box.addWidget(self.session_step)
        self.stop_button = QPushButton("Stop presenting")
        self.stop_button.setObjectName("danger")
        self.stop_button.setEnabled(False)
        box.addWidget(self.stop_button)
        layout.addWidget(frame)
        frame, box = card()
        box.addWidget(label("You're always in control", "subheading"))
        box.addWidget(
            label(
                "Close your fist to lock gestures. Ctrl + Alt + Space stops "
                "presenting from anywhere. Switching to another window pauses "
                "PalmCue automatically."
            )
        )
        box.addWidget(
            label(
                "Slides use the left and right arrow keys. The pointer moves your "
                "mouse. Optional zoom uses Ctrl + plus / minus and depends on "
                "your presentation app. Rehearse with your actual slides first.",
                "muted",
            )
        )
        layout.addWidget(frame)
        layout.addStretch()

    def build_guide(self):
        layout = self.page(
            "A FEW DELIBERATE MOVEMENTS",
            "Find your next cue.",
            "Face your palm toward the camera. Keep unused fingers and your thumb "
            "tucked in for the finger-count gestures.",
        )
        grid = QGridLayout()
        entries = [
            ("open", "Unlock", "Hold an open palm still for a moment, then relax your fingers."),
            ("fist", "Lock", "Close your fist briefly. Works anywhere in the camera view."),
            (
                "two",
                "Next slide · Reliable",
                "Hold up your index and middle fingers until the bar fills.",
            ),
            ("three", "Previous slide · Reliable", "Hold up your index, middle and ring fingers."),
            ("point", "Pointer", "Raise just your index finger and move it gently."),
            (
                "pinch",
                "Click · optional",
                "Point first, then touch thumb to index. Keep other fingers tucked.",
            ),
            (
                "swipe",
                "Slides · Showcase",
                "Hold two fingers briefly, then swipe right for next or left for previous.",
            ),
            (
                "zoom",
                "Zoom · Showcase, optional",
                "Hold five fingers open, then spread or bring them closer. Keep your palm still.",
            ),
        ]
        for i, (kind, title, description) in enumerate(entries):
            frame, box = card()
            line = QHBoxLayout()
            line.addWidget(GesturePreview(kind))
            text = QVBoxLayout()
            text.addWidget(label(title, "subheading"))
            text.addWidget(label(description, "muted"))
            line.addLayout(text, 1)
            box.addLayout(line)
            grid.addWidget(frame, i // 2, i % 2)
        layout.addLayout(grid)
        layout.addWidget(
            label(
                "Between slide commands, open your palm for a brief moment. "
                "Keeping a gesture held will never race through your slides.",
                "muted",
            )
        )
        layout.addStretch()

    def build_preferences(self):
        layout = self.page(
            "MAKE IT FEEL NATURAL",
            "A setup that fits you.",
            "Changes save automatically and lock controls for safety.",
        )
        frame, box = card()
        box.addWidget(label("Gesture style", "subheading"))
        self.mode = QComboBox()
        self.mode.addItem("Reliable · deliberate holds (recommended)", "reliable")
        self.mode.addItem("Showcase · expressive swipes", "showcase")
        self.mode.setCurrentIndex(self.mode.findData(self.settings.mode))
        self.mode.setAccessibleName("Gesture style")
        box.addWidget(self.mode)
        box.addWidget(
            label(
                "Reliable uses two fingers for next and three for previous. "
                "Showcase uses two-finger swipes instead.",
                "muted",
            )
        )
        self.hold_label = label("Hold time", "subheading")
        box.addWidget(self.hold_label)
        self.hold = QSlider(Qt.Orientation.Horizontal)
        self.hold.setRange(6, 15)
        self.hold.setValue(round(self.settings.hold_seconds * 10))
        self.hold.setAccessibleName("Hold time: faster to more deliberate")
        box.addWidget(self.hold)
        box.addWidget(label("Faster                                      More deliberate", "muted"))
        for key, title in (
            ("pointer", "Use index finger as a pointer"),
            ("click", "Allow pinch to click"),
            ("zoom", "Allow five-finger zoom in Showcase"),
        ):
            check = QCheckBox(title)
            check.setChecked(getattr(self.settings, key))
            setattr(self, key + "_check", check)
            check.toggled.connect(lambda value, name=key: self.update_setting(**{name: value}))
            box.addWidget(check)
        box.addWidget(
            label(
                "Click and zoom start off. Click may advance a slide or open a link. "
                "Zoom works only in apps that support Ctrl + plus / minus.",
                "muted",
            )
        )
        layout.addWidget(frame)
        frame, box = card()
        box.addWidget(label("Camera & gesture area", "subheading"))
        self.cameras = QComboBox()
        self.cameras.addItem("Automatic · find an available webcam", -1)
        if self.settings.camera >= 0:
            self.cameras.addItem(f"Camera {self.settings.camera + 1}", self.settings.camera)
            self.cameras.setCurrentIndex(1)
        self.cameras.setAccessibleName("Webcam")
        box.addWidget(self.cameras)
        self.scan_button = QPushButton("Find connected cameras")
        box.addWidget(self.scan_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.area = QComboBox()
        for title, key in (
            ("Center (recommended)", "center"),
            ("Left side", "left"),
            ("Right side", "right"),
            ("Wider area", "wide"),
        ):
            self.area.addItem(title, key)
        self.area.setCurrentIndex(self.area.findData(self.settings.area))
        self.area.setAccessibleName("Gesture activation area")
        box.addWidget(self.area)
        box.addWidget(
            label(
                "The dashed box in Practice shows where your palm activates gestures. "
                "Choose the side where you naturally hold your hand.",
                "muted",
            )
        )
        self.mirror = QCheckBox("Mirror the camera, like looking in a mirror")
        self.mirror.setChecked(self.settings.mirror)
        box.addWidget(self.mirror)
        self.debug_preview_check = QCheckBox("Show tracking landmarks in the camera preview")
        self.debug_preview_check.setChecked(self.settings.debug_preview)
        self.debug_preview_check.setToolTip(
            "Advanced troubleshooting view. It stays off during presentations."
        )
        box.addWidget(self.debug_preview_check)
        box.addWidget(
            label(
                "Advanced: shows the 21 points PalmCue reads. This helps diagnose lighting or "
                "hand position and does not change gesture decisions.",
                "muted",
            )
        )
        layout.addWidget(frame)
        self.mode.currentIndexChanged.connect(
            lambda: self.update_setting(mode=self.mode.currentData())
        )
        self.area.currentIndexChanged.connect(
            lambda: self.update_setting(area=self.area.currentData())
        )
        self.hold.valueChanged.connect(lambda v: self.update_setting(hold_seconds=v / 10))
        self.mirror.toggled.connect(lambda v: self.update_setting(mirror=v))
        self.debug_preview_check.toggled.connect(lambda v: self.update_setting(debug_preview=v))
        self.auto_present_check.toggled.connect(lambda v: self.update_setting(auto_present=v))
        self.cameras.currentIndexChanged.connect(
            lambda: self.update_setting(camera=self.cameras.currentData())
        )
        self.refresh_preference_labels()
        layout.addStretch()

    def refresh_preference_labels(self):
        self.hold_label.setText(f"Hold time · {self.settings.hold_seconds:.1f} seconds")
        self.hold.setEnabled(self.settings.mode == "reliable")
        self.zoom_check.setEnabled(self.settings.mode == "showcase")
        self.click_check.setEnabled(self.settings.pointer)

    def update_setting(self, **changes):
        self.settings = replace(self.settings, **changes)
        self.preview.area = self.settings.area
        self.preview.debug = self.settings.debug_preview
        self.preview.update()
        self.refresh_preference_labels()
        if hasattr(self, "runtime"):
            self.runtime.reconfigure(changes)
        try:
            save_settings(self.settings_path, self.settings)
        except OSError:
            self.show_notice(
                "Your changes work for this session, but could not be saved. "
                "Check that your user folder is writable."
            )

    def show_notice(self, message):
        self.notice.setText(message)
        self.notice.setVisible(bool(message))

    def closeEvent(self, event):
        self.runtime.close()
        event.accept()

    def build_help(self):
        layout = self.page(
            "A LITTLE HELP",
            "Ready for the room.",
            "A quick rehearsal makes for a calmer presentation.",
        )
        for title, text in [
            (
                "If your hand isn't responding",
                "Face a light, avoid a bright window behind you, "
                "and show your whole hand. Keep one hand in the dashed area. Hold an open palm to "
                "unlock, then relax your fingers before a command. Try a wider area if needed.",
            ),
            (
                "If the camera won't start",
                "Close apps using your camera. In Windows Settings, "
                "open Privacy & security → Camera and enable camera access for desktop apps. "
                "Reconnect your webcam and choose Start camera or Retry.",
            ),
            (
                "If your slides don't respond",
                "Start slideshow mode before choosing the presentation "
                "window. Refresh the list, select the slideshow itself, then start presenting. "
                "Bring it to the front during the countdown. "
                "PalmCue pauses when you switch windows. "
                "Apps running as administrator may block input.",
            ),
            (
                "Before your audience arrives",
                "Try next, previous and pointer in your actual deck. "
                "Full-screen apps may hide the mouse; move your index finger to reveal it. "
                "Keep click and zoom off unless you have rehearsed them. "
                "Keep your usual keyboard or clicker nearby.",
            ),
            (
                "Your privacy",
                "Video is processed on your computer and never saved or uploaded. "
                "PalmCue does not use your microphone. Stop the camera or quit to release it. "
                "Only your preferences are saved.",
            ),
        ]:
            frame, box = card()
            box.addWidget(label(title, "subheading"))
            box.addWidget(label(text, "muted"))
            layout.addWidget(frame)
        self.diagnostics = label("Advanced diagnostics · no session started", "muted")
        self.diagnostics.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.diagnostics.hide()
        debug = QPushButton("Show advanced diagnostics")
        debug.clicked.connect(lambda: self.diagnostics.setVisible(not self.diagnostics.isVisible()))
        layout.addWidget(debug, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.diagnostics)
        layout.addStretch()
