# Sticky Focus Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign KeenPie's desktop sticky overlay into a readable semi-transparent focus panel with list and active-task modes while remembering the user's preferred task time input mode.

**Architecture:** Keep persistent preferences in `app/config.py` through `QSettings`, keep current execution context lightweight instead of adding a task execution history table, and split pure sticky sizing/state decisions into testable helpers before changing `StickyOverlay` painting and mouse handling. The existing `MainWindow` remains the coordinator between task pages and the overlay.

**Tech Stack:** Python 3, PySide6 Widgets/QPainter/QSettings, SQLite task data, `unittest`

---

## File Map

- Modify `app/config.py`: add validated input-time-mode, sticky width, sticky view-mode, and active-task context settings helpers.
- Modify `app/pages/home_page.py`: initialize the time mode from settings and persist changes when radio buttons are clicked.
- Create `app/sticky_state.py`: keep sticky width bounds, view-mode validation, next-task selection, active-task context decisions, and encouragement messages outside the painter widget.
- Modify `app/sticky_overlay.py`: replace background-sampling readability with a semi-transparent panel, render list and active-task modes, add mode/start hit targets, and support horizontal resize.
- Modify `app/main_window.py`: clear invalid active-task context after task changes and keep overlay reload behavior coherent.
- Create `tests/test_config_preferences.py`: settings tests for time input mode, sticky width/view mode, and active-task context.
- Create `tests/test_sticky_state.py`: pure tests for task selection, width clamping, view-mode validation, and active-task invalidation.
- Extend offscreen verification through command-line snippets in the final task rather than adding brittle paint snapshot tests.

## Scope Guard

This plan does not implement nightly reviews, review forms, focus analytics, or a complex reminder cadence. It only leaves the active task state in a form that later review work can build on.

### Task 1: Add Sticky And Input Preferences

**Files:**
- Modify: `app/config.py`
- Create: `tests/test_config_preferences.py`

- [ ] **Step 1: Write failing settings tests**

```python
import unittest
from PySide6.QtCore import QCoreApplication, QSettings

from app import config


class PreferenceSettingsTest(unittest.TestCase):
    def setUp(self):
        QCoreApplication.setOrganizationName("KeenPieTests")
        QCoreApplication.setApplicationName("StickyFocusPreferences")
        self._settings = QSettings("KeenPieTests", "StickyFocusPreferences")
        self._settings.clear()
        self._old_settings = config.SETTINGS
        config.SETTINGS = self._settings

    def tearDown(self):
        self._settings.clear()
        config.SETTINGS = self._old_settings

    def test_input_mode_defaults_and_rejects_unknown_values(self):
        self.assertEqual(config.get_input_time_mode(), "precise")

        config.set_input_time_mode("none")
        self.assertEqual(config.get_input_time_mode(), "none")

        config.SETTINGS.setValue("task/input_time_mode", "strange")
        self.assertEqual(config.get_input_time_mode(), "precise")

    def test_sticky_width_is_clamped(self):
        config.SETTINGS.setValue("sticky/width", 120)
        self.assertEqual(config.get_sticky_width(), config.STICKY_MIN_WIDTH)

        config.SETTINGS.setValue("sticky/width", 9999)
        self.assertEqual(config.get_sticky_width(), config.STICKY_MAX_WIDTH)

    def test_active_task_context_round_trips(self):
        config.set_active_task(42, "2026-05-21T09:30:00")

        self.assertEqual(config.get_active_task_id(), 42)
        self.assertEqual(config.get_active_started_at(), "2026-05-21T09:30:00")

        config.clear_active_task()
        self.assertIsNone(config.get_active_task_id())
        self.assertIsNone(config.get_active_started_at())
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_config_preferences
```

Expected: FAIL because `get_input_time_mode`, sticky constants, and active-task helpers do not exist yet.

- [ ] **Step 3: Add validated preference helpers**

Add these definitions to `app/config.py`:

```python
INPUT_TIME_MODES = {"none", "period", "precise"}
STICKY_VIEW_MODES = {"list", "active"}
STICKY_MIN_WIDTH = 280
STICKY_DEFAULT_WIDTH = 360
STICKY_MAX_WIDTH = 680


def get_input_time_mode() -> str:
    mode = SETTINGS.value("task/input_time_mode", "precise")
    return mode if mode in INPUT_TIME_MODES else "precise"


def set_input_time_mode(mode: str):
    if mode in INPUT_TIME_MODES:
        SETTINGS.setValue("task/input_time_mode", mode)


def _clamp_sticky_width(width: int) -> int:
    return max(STICKY_MIN_WIDTH, min(STICKY_MAX_WIDTH, width))


def get_sticky_width() -> int:
    return _clamp_sticky_width(int(SETTINGS.value("sticky/width", STICKY_DEFAULT_WIDTH)))


def set_sticky_width(width: int):
    SETTINGS.setValue("sticky/width", _clamp_sticky_width(int(width)))


def get_sticky_view_mode() -> str:
    mode = SETTINGS.value("sticky/view_mode", "list")
    return mode if mode in STICKY_VIEW_MODES else "list"


def set_sticky_view_mode(mode: str):
    if mode in STICKY_VIEW_MODES:
        SETTINGS.setValue("sticky/view_mode", mode)


def get_active_task_id() -> int | None:
    value = SETTINGS.value("sticky/active_task_id")
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_active_started_at() -> str | None:
    value = SETTINGS.value("sticky/active_started_at")
    return str(value) if value else None


def set_active_task(task_id: int, started_at: str):
    SETTINGS.setValue("sticky/active_task_id", int(task_id))
    SETTINGS.setValue("sticky/active_started_at", started_at)


def clear_active_task():
    SETTINGS.remove("sticky/active_task_id")
    SETTINGS.remove("sticky/active_started_at")
```

- [ ] **Step 4: Run the settings tests and verify they pass**

Run:

```powershell
python -m unittest tests.test_config_preferences
```

Expected: PASS.

- [ ] **Step 5: Commit the preference layer**

```powershell
git add app/config.py tests/test_config_preferences.py
git commit -m "Add sticky focus preferences"
```

### Task 2: Remember The Home Page Time Input Mode

**Files:**
- Modify: `app/pages/home_page.py`
- Test: `tests/test_config_preferences.py`

- [ ] **Step 1: Add a failing integration assertion for the saved mode**

Append to `tests/test_config_preferences.py`:

```python
    def test_home_page_mode_can_be_seeded_from_saved_preference(self):
        config.set_input_time_mode("none")
        self.assertEqual(config.get_input_time_mode(), "none")
```

This test intentionally stays at the settings boundary because `HomePage` performs database work during construction. The Qt offscreen smoke test in Task 6 verifies the widget wiring.

- [ ] **Step 2: Run the focused preference tests**

Run:

```powershell
python -m unittest tests.test_config_preferences
```

Expected: PASS for the settings boundary; this confirms the preference API is ready before widget wiring changes.

- [ ] **Step 3: Wire `HomePage` to the preference API**

Update the imports and mode handling in `app/pages/home_page.py`:

```python
from app.config import get_input_time_mode, set_input_time_mode
```

Replace the initial mode assignment:

```python
self._time_mode = get_input_time_mode()
```

Persist changes inside `_on_mode_changed`:

```python
def _on_mode_changed(self, btn):
    self._time_mode = btn.property("mode")
    set_input_time_mode(self._time_mode)
    for row in self._task_rows:
        row.set_time_mode(self._time_mode)
        row._on_changed()
```

- [ ] **Step 4: Run the preference tests and a compile check**

Run:

```powershell
python -m unittest tests.test_config_preferences
python -m compileall app/pages/home_page.py
```

Expected: both commands exit 0.

- [ ] **Step 5: Commit the home-page preference wiring**

```powershell
git add app/pages/home_page.py tests/test_config_preferences.py
git commit -m "Remember task input time mode"
```

### Task 3: Add Testable Sticky Focus State Helpers

**Files:**
- Create: `app/sticky_state.py`
- Create: `tests/test_sticky_state.py`

- [ ] **Step 1: Write failing sticky-state tests**

```python
import unittest

from app.sticky_state import (
    complete_message,
    get_active_task,
    get_next_task,
    normalize_view_mode,
    resize_width,
)


TASKS = [
    {"id": 1, "content": "写周报", "status": "pending"},
    {"id": 2, "content": "听英语", "status": "pending"},
    {"id": 3, "content": "已完成", "status": "done"},
]


class StickyStateTest(unittest.TestCase):
    def test_active_task_is_found_only_when_pending(self):
        self.assertEqual(get_active_task(TASKS, 2)["content"], "听英语")
        self.assertIsNone(get_active_task(TASKS, 3))
        self.assertIsNone(get_active_task(TASKS, 99))

    def test_next_task_skips_the_active_task(self):
        self.assertEqual(get_next_task(TASKS, 1)["id"], 2)
        self.assertEqual(get_next_task(TASKS, None)["id"], 1)

    def test_view_mode_falls_back_to_list_without_active_task(self):
        self.assertEqual(normalize_view_mode("active", None), "list")
        self.assertEqual(normalize_view_mode("active", TASKS[0]), "active")
        self.assertEqual(normalize_view_mode("unknown", TASKS[0]), "list")

    def test_resize_width_clamps_bounds(self):
        self.assertEqual(resize_width(360, 40), 400)
        self.assertEqual(resize_width(280, -50), 280)
        self.assertEqual(resize_width(680, 50), 680)

    def test_completion_message_is_encouraging(self):
        self.assertIn("推进", complete_message("写周报"))
```

- [ ] **Step 2: Run the new sticky-state tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_sticky_state
```

Expected: FAIL because `app.sticky_state` does not exist yet.

- [ ] **Step 3: Add the pure sticky-state helper module**

Create `app/sticky_state.py`:

```python
from app.config import STICKY_MAX_WIDTH, STICKY_MIN_WIDTH


def get_active_task(tasks: list[dict], active_task_id: int | None) -> dict | None:
    for task in tasks:
        if task.get("id") == active_task_id and task.get("status") == "pending":
            return task
    return None


def get_next_task(tasks: list[dict], active_task_id: int | None) -> dict | None:
    for task in tasks:
        if task.get("status") == "pending" and task.get("id") != active_task_id:
            return task
    return None


def normalize_view_mode(view_mode: str, active_task: dict | None) -> str:
    if view_mode == "active" and active_task:
        return "active"
    return "list"


def resize_width(width: int, delta_x: int) -> int:
    return max(STICKY_MIN_WIDTH, min(STICKY_MAX_WIDTH, width + delta_x))


def start_message(task: dict) -> str:
    return f"先把「{task['content']}」推进一点。"


def complete_message(content: str) -> str:
    return f"「{content}」已经推进完成。"
```

- [ ] **Step 4: Run the sticky-state tests**

Run:

```powershell
python -m unittest tests.test_sticky_state
```

Expected: PASS.

- [ ] **Step 5: Commit the state helpers**

```powershell
git add app/sticky_state.py tests/test_sticky_state.py
git commit -m "Add sticky focus state helpers"
```

### Task 4: Redesign Focus List Overlay Readability And Resizing

**Files:**
- Modify: `app/sticky_overlay.py`
- Modify: `app/config.py`
- Test: `tests/test_sticky_state.py`

- [ ] **Step 1: Add a failing width persistence expectation**

Append to `tests/test_config_preferences.py`:

```python
    def test_sticky_width_round_trips_after_resize_save(self):
        config.set_sticky_width(412)
        self.assertEqual(config.get_sticky_width(), 412)
```

- [ ] **Step 2: Run the preference tests**

Run:

```powershell
python -m unittest tests.test_config_preferences
```

Expected: PASS after Task 1 because the storage API already supports the new width. This confirms the state boundary before painter wiring changes.

- [ ] **Step 3: Replace sampling-driven readability with a panel-driven painter**

In `app/sticky_overlay.py`:

1. Remove imports from `app.color_adapt`.
2. Remove `_text_colors`, `_refresh_timer`, `_refresh_colors`, and background-sampled text-color branches.
3. Import the sticky width helpers:

```python
from app.config import (
    get_active_task_id,
    get_display_count,
    get_font_size,
    get_overdue_color,
    get_sticky_view_mode,
    get_sticky_width,
    get_transparency,
    set_sticky_width,
)
from app.sticky_state import resize_width
```

4. Keep list-mode text colors stable:

```python
TASK_TEXT = QColor("#f4f7fb")
META_TEXT = QColor("#aeb7c2")
PANEL_BORDER = QColor(255, 255, 255, 30)
```

5. Use a panel in all states:

```python
panel_alpha = 232 if self._hovered else max(132, int((100 - get_transparency()) / 100.0 * 110) + 132)
painter.setBrush(QColor(18, 22, 28, panel_alpha))
painter.setPen(QPen(PANEL_BORDER, 1))
painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
```

6. Initialize width from settings and stop fixing the width in `_update_size`:

```python
self._panel_width = get_sticky_width()
self.setMinimumWidth(self._panel_width)
```

```python
def _update_size(self):
    row_h = self._font_size + 20
    title_h = 40
    count = max(len(self._tasks), 1)
    self.setFixedSize(self._panel_width, title_h + count * row_h + 12)
```

- [ ] **Step 4: Add horizontal resize mouse handling**

Add widget state:

```python
self._resize_anchor: QPoint | None = None
self._resize_start_width = self._panel_width
self._resize_rect = QRect()
```

Expose the hit area while painting:

```python
self._resize_rect = QRect(w - 10, 36, 10, h - 46)
if self._hovered:
    painter.setPen(QPen(QColor("#6f7b88"), 1))
    painter.drawLine(w - 6, 48, w - 6, h - 18)
```

Handle drag from that hit area:

```python
if self._resize_rect.contains(event.pos()):
    self._resize_anchor = event.globalPosition().toPoint()
    self._resize_start_width = self._panel_width
    return
```

```python
if self._resize_anchor is not None:
    delta_x = event.globalPosition().toPoint().x() - self._resize_anchor.x()
    self._panel_width = resize_width(self._resize_start_width, delta_x)
    self._update_size()
    self.update()
    return
```

```python
if self._resize_anchor is not None:
    set_sticky_width(self._panel_width)
self._resize_anchor = None
```

- [ ] **Step 5: Run unit and compile checks**

Run:

```powershell
python -m unittest tests.test_config_preferences tests.test_sticky_state
python -m compileall app/sticky_overlay.py
```

Expected: both commands exit 0.

- [ ] **Step 6: Commit the readable resizable list overlay**

```powershell
git add app/config.py app/sticky_overlay.py tests/test_config_preferences.py tests/test_sticky_state.py
git commit -m "Redesign sticky focus panel"
```

### Task 5: Add Active Task Mode And Lightweight Encouragement

**Files:**
- Modify: `app/sticky_overlay.py`
- Modify: `app/main_window.py`
- Test: `tests/test_sticky_state.py`

- [ ] **Step 1: Add a failing invalid-active-state test**

Append to `tests/test_sticky_state.py`:

```python
    def test_missing_active_task_returns_list_mode(self):
        missing = get_active_task(TASKS, 77)
        self.assertIsNone(missing)
        self.assertEqual(normalize_view_mode("active", missing), "list")
```

- [ ] **Step 2: Run the sticky-state tests**

Run:

```powershell
python -m unittest tests.test_sticky_state
```

Expected: PASS if the fallback behavior from Task 3 is present. This fixes the state contract before widget integration.

- [ ] **Step 3: Add active-task overlay state and hit targets**

In `app/sticky_overlay.py`, import:

```python
from datetime import datetime
from app.config import (
    clear_active_task,
    get_active_started_at,
    set_active_task,
    set_sticky_view_mode,
)
from app.sticky_state import (
    complete_message,
    get_active_task,
    get_next_task,
    normalize_view_mode,
    start_message,
)
```

Add fields:

```python
self._active_task = None
self._next_task = None
self._view_mode = get_sticky_view_mode()
self._mode_rect = QRect()
self._start_rects: list[QRect] = []
self._complete_rect = QRect()
self._message = ""
```

Resolve current state inside `load_tasks`:

```python
self._active_task = get_active_task(self._tasks, get_active_task_id())
self._next_task = get_next_task(self._tasks, get_active_task_id())
self._view_mode = normalize_view_mode(get_sticky_view_mode(), self._active_task)
if self._view_mode == "list" and get_active_task_id() and not self._active_task:
    clear_active_task()
```

- [ ] **Step 4: Render the two modes**

Keep the focus-list painter as `_paint_list_mode(painter, title_h, row_h)`.

Add active-mode painter:

```python
def _paint_active_mode(self, painter: QPainter, title_h: int):
    task = self._active_task
    content = task["content"] if task else "还没有开始的事项"
    painter.setPen(QColor("#72e5ad"))
    painter.setFont(_ui_font(11, QFont.Weight.DemiBold))
    painter.drawText(18, title_h + 10, self.width() - 36, 18, Qt.AlignmentFlag.AlignVCenter, "现在做")
    painter.setPen(QColor("#f4f7fb"))
    painter.setFont(_ui_font(self._font_size + 3, QFont.Weight.Bold))
    painter.drawText(18, title_h + 34, self.width() - 36, 34, Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine, content)
    if task:
        painter.setPen(QColor("#aeb7c2"))
        painter.setFont(_ui_font(11, QFont.Weight.Medium))
        meta = f"{task.get('category') or '生活'} · 开始于 {get_active_started_at() or '刚刚'}"
        painter.drawText(18, title_h + 72, self.width() - 36, 18, Qt.AlignmentFlag.AlignVCenter, meta)
        self._complete_rect = QRect(18, title_h + 104, 72, 28)
```

For list mode, paint a small start affordance on hover for each row and store its rectangle in `_start_rects`.

- [ ] **Step 5: Wire mode switching, start, and complete actions**

Use mouse hit targets:

```python
if self._mode_rect.contains(event.pos()):
    self._view_mode = "list" if self._view_mode == "active" else "active"
    self._view_mode = normalize_view_mode(self._view_mode, self._active_task)
    set_sticky_view_mode(self._view_mode)
    self._update_size()
    self.update()
    return
```

```python
for i, rect in enumerate(self._start_rects):
    if rect.contains(event.pos()) and i < len(self._tasks):
        task = self._tasks[i]
        set_active_task(task["id"], datetime.now().strftime("%H:%M"))
        set_sticky_view_mode("active")
        self._message = start_message(task)
        self.load_tasks(self._target_date)
        return
```

```python
if self._complete_rect.contains(event.pos()) and self._active_task:
    task = self._active_task
    update_task_status(task["id"], "done")
    clear_active_task()
    self._message = complete_message(task["content"])
    self.done_toggled.emit(task["id"], "done")
    self.load_tasks(self._target_date)
    return
```

Store the loaded target date in `load_tasks`:

```python
self._target_date = target_date
```

- [ ] **Step 6: Clear stale active task context from the main window refresh path**

In `app/main_window.py`, keep `_on_sticky_done` and `_on_tasks_changed` reloading the overlay after task changes. If the active task disappears, `StickyOverlay.load_tasks` clears context through its state contract.

- [ ] **Step 7: Run tests and compile checks**

Run:

```powershell
python -m unittest tests.test_config_preferences tests.test_sticky_state tests.test_db_categories
python -m compileall app tests
```

Expected: all commands exit 0.

- [ ] **Step 8: Commit active task mode**

```powershell
git add app/sticky_overlay.py app/main_window.py tests/test_sticky_state.py
git commit -m "Add sticky active task mode"
```

### Task 6: Verify The Release Slice End To End

**Files:**
- Verify: `app/config.py`
- Verify: `app/pages/home_page.py`
- Verify: `app/sticky_overlay.py`
- Verify: `app/main_window.py`

- [ ] **Step 1: Run the full automated check set**

Run:

```powershell
python -m unittest tests.test_config_preferences tests.test_sticky_state tests.test_db_categories
python -m compileall main.py app tests
git diff --check
```

Expected: unit tests PASS, compileall exits 0, and `git diff --check` reports no whitespace errors.

- [ ] **Step 2: Run an offscreen widget smoke test**

Run:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
@'
import sys
from PySide6.QtWidgets import QApplication
from app.db import init_db
from app.main_window import MainWindow
from app.sticky_overlay import StickyOverlay

app = QApplication(sys.argv)
init_db()
window = MainWindow()
for index in range(3):
    window._switch_page(index)
    app.processEvents()

sticky = StickyOverlay()
sticky._tasks = [
    {"id": 1, "content": "写周报", "category": "工作", "time_label": None, "time_value": None, "status": "pending"},
    {"id": 2, "content": "英语听力", "category": "学习", "time_label": "晚上", "time_value": None, "status": "pending"},
]
sticky._update_size()
sticky.show()
app.processEvents()
print(f"pages_ok=3 sticky_size={sticky.width()}x{sticky.height()}")
sticky.close()
window.close()
app.quit()
'@ | python -
```

Expected: output includes `pages_ok=3` and a sticky size inside the width clamp bounds.

- [ ] **Step 3: Run a manual Windows verification pass**

Run the app:

```powershell
python main.py
```

Verify:

1. Select `无时间`, close and reopen the app, and confirm home-page time mode remains `无时间`.
2. Open the sticky overlay on a bright desktop background and confirm the text sits on a readable semi-transparent panel without white-on-white flash.
3. Drag the sticky width handle left and right and confirm task text has more or less room without collapsing below the minimum width.
4. Start a task from focus list mode and confirm active mode shows the current task and next-task hint.
5. Complete the active task and confirm the overlay returns to valid remaining-task state.

- [ ] **Step 4: Commit any verification fixes**

If verification requires a targeted fix, add only the affected files and commit:

```powershell
git add app tests
git commit -m "Polish sticky focus verification"
```

If no fix is needed, do not create an empty commit.
