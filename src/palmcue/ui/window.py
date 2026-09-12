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
        self.setMinimumSize(820, 600)
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
        brand_icon = label("")
        brand_icon.setPixmap(app_icon().pixmap(64, 64))
        side.addWidget(brand_icon)
        side.addWidget(label("PalmCue", "brand"))
        side.addWidget(label("PRESENT WITH PRESENCE", "tagline"))
        side.addSpacing(35)
        self.nav = QButtonGroup(self)
        self.stack = QStackedWidget()
        for i, name in enumerate(
            ("Camera & practice", "Present", "Gesture guide", "Preferences", "Help")
        ):
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
            "GET READY",
            "Your camera. Your next cue.",
            "Start your camera, try a gesture, then open your slides in fullscreen.",
        )
        self.welcome, box = card()
        self.welcome.setObjectName("banner")
        box.addWidget(label("Your first cue, in three small steps", "subheading"))
        box.addWidget(
            label(
                "1  Start your camera.\n2  Hold two fingers for next.\n"
                "3  Open your hand briefly between commands."
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
        self.gesture_status = label("Practice starts paused · hold an open palm", "subheading")
        practice_layout.addWidget(self.gesture_status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Gesture hold progress")
        practice_layout.addWidget(self.progress)
        self.last_action = label("Waiting for your first cue", "muted")
        practice_layout.addWidget(self.last_action)
        self.lock_button = QPushButton("Pause gestures")
        practice_layout.addWidget(self.lock_button)
        row.addWidget(practice_card, 5)
        layout.addLayout(row)
        next_step = QPushButton("Ready? Set up your presentation →")
        next_step.setObjectName("primary")
        next_step.clicked.connect(lambda: self.navigate(1))
        layout.addWidget(next_step)
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
            "PRESENT WITH ONE SCREEN",
            "Stay with your slides.",
            "A small panel over your slides shows the countdown, hand feedback, and commands.",
        )
        frame, box = card()
        box.addWidget(label("1. Camera on   2. Slides fullscreen   3. Present", "subheading"))
        self.present_camera_button = QPushButton("Start camera")
        self.present_camera_button.setObjectName("primary")
        self.present_camera_button.clicked.connect(lambda: self.runtime.toggle_camera())
        box.addWidget(self.present_camera_button)
        self.auto_present_check = QCheckBox("Start automatically when slides go fullscreen")
        self.auto_present_check.setChecked(self.settings.auto_present)
        box.addWidget(self.auto_present_check)
        box.addWidget(
            label(
                "In Canva, choose Present and enter fullscreen. Keep your slides in front "
                "during the countdown. Gestures are ready when it finishes. "
                "Fullscreen detection also works with supported browsers, "
                "PowerPoint and PDF viewers.",
                "muted",
            )
        )
        box.addWidget(
            label(
                "Fastest control: raise an open hand briefly, then flick your wrist "
                "right for next or left for previous. Lower your hand between cues.",
                "subheading",
            )
        )
        self.feedback_check = QCheckBox("Show feedback over my slides")
        self.feedback_check.setChecked(self.settings.presentation_feedback)
        self.feedback_check.toggled.connect(lambda v: self.update_setting(presentation_feedback=v))
        box.addWidget(self.feedback_check)
        preview_feedback = QPushButton("Preview on-screen feedback")
        preview_feedback.clicked.connect(self.preview_feedback)
        box.addWidget(preview_feedback, alignment=Qt.AlignmentFlag.AlignLeft)
        box.addWidget(
            label(
                "Visible on this screen and in full-screen sharing. "
                "Turn off for a clean audience view.",
                "muted",
            )
        )
        self.session_step = label("Start your camera to get ready", "badge")
        box.addWidget(self.session_step)
        self.session_status = label("Your camera is off.", "muted")
        box.addWidget(self.session_status)
        self.stop_button = QPushButton("Stop presenting")
        self.stop_button.setObjectName("danger")
        self.stop_button.setEnabled(False)
        box.addWidget(self.stop_button)
        layout.addWidget(frame)
        manual_toggle = QCheckBox("Choose a window manually instead")
        layout.addWidget(manual_toggle)
        frame, box = card()
        frame.setVisible(False)
        manual_toggle.toggled.connect(frame.setVisible)
        box.addWidget(label("Choose your presentation window", "subheading"))
        self.targets = QComboBox()
        self.targets.setAccessibleName("Presentation window")
        self.targets.addItem("Open your presentation, then refresh", None)
        box.addWidget(self.targets)
        self.refresh_targets = QPushButton("Refresh windows")
        box.addWidget(self.refresh_targets, alignment=Qt.AlignmentFlag.AlignLeft)
        box.addWidget(
            label(
                "After Start, you have five seconds to bring that window to the "
                "front. Gestures become ready when the countdown finishes."
            )
        )
        self.present_button = QPushButton("Start presenting")
        self.present_button.setObjectName("primary")
        self.present_button.setEnabled(False)
        box.addWidget(self.present_button)
        layout.addWidget(frame)
        frame, box = card()
        box.addWidget(label("You're always in control", "subheading"))
        box.addWidget(
            label(
                "Relax or lower your hand briefly between commands. "
                "Ctrl + Alt + Space stops "
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

    def preview_feedback(self):
        from palmcue.ui.hud import PresentationHUD

        if not hasattr(self, "feedback_preview"):
            self.feedback_preview = PresentationHUD()
        self.feedback_preview.place(self.frameGeometry().center())
        self.feedback_preview.display(
            "PalmCue · Locked",
            "Hold an open palm to unlock · this is a preview",
            0.6,
            temporary=True,
        )

    def build_guide(self):
        layout = self.page(
            "A FEW DELIBERATE MOVEMENTS",
            "Find your next cue.",
            "Face your palm toward the camera. Keep unused fingers and your thumb "
            "tucked in for the finger-count gestures.",
        )
        grid = QGridLayout()
        entries = [
            (
                "open",
                "Wrist flick · Recommended",
                "In a presentation, briefly steady an open hand, then slide it left or right.",
            ),
            ("fist", "No presentation action", "A fist is ignored while presenting."),
            (
                "two",
                "Next slide · Reliable",
                "Briefly show your index and middle fingers.",
            ),
            (
                "three",
                "Previous slide · Reliable",
                "Use the German three: thumb, index and middle finger.",
            ),
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
        self.mode.addItem("Simple · wrist flicks with finger-pose fallback", "reliable")
        self.mode.addItem("Showcase · expressive swipes", "showcase")
        self.mode.setCurrentIndex(self.mode.findData(self.settings.mode))
        self.mode.setAccessibleName("Gesture style")
        box.addWidget(self.mode)
        box.addWidget(
            label(
                "An open-hand wrist flick controls slides in either style. Simple also accepts "
                "brief finger poses; Showcase adds two-finger swipes.",
                "muted",
            )
        )
        self.hold_label = label("Hold time", "subheading")
        box.addWidget(self.hold_label)
        self.hold = QSlider(Qt.Orientation.Horizontal)
        self.hold.setRange(3, 9)
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
        if hasattr(self, "feedback_preview"):
            self.feedback_preview.close()
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
                "and show your whole hand. Keep one hand in the dashed area. Practice starts "
                "paused; presentations start ready. Try a wider area if needed.",
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
