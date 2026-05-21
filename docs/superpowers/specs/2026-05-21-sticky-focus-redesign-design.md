# Sticky Focus Redesign Design

## Goal

KeenPie should move from a task input panel plus a fragile transparent overlay toward a desktop companion that stays readable, helps the user stay on the current task, and still feels lightweight for daily use.

The first release of this redesign focuses on the desktop sticky overlay. It also includes a small input habit improvement so the main task entry flow better matches repeated daily use.

## User Priorities

1. Redesign the desktop sticky overlay first.
2. Improve task execution support and encouragement as a secondary concern.
3. Remember the user's preferred task input time mode as a smaller companion improvement.
4. Keep daily review as a later phase rather than expanding the first release too far.

## Product Direction

The selected product direction is `Today Focus`.

KeenPie should help the user answer:

- What should I do today?
- What am I doing right now?
- What comes next after I finish?

The sticky overlay should support two switchable modes:

- Focus list mode for today's pending work.
- Active task mode for the task currently being executed.

## Sticky Overlay Experience

### Visual Direction

The selected sticky style is a semi-transparent floating panel.

The overlay should provide its own readable surface instead of relying on background sampling to decide whether text is visible. This avoids the current failure mode where desktop text, bright backgrounds, or delayed sampling produce low-contrast task text.

The overlay should use:

- A dark semi-transparent panel background.
- High-contrast light task text.
- A subtle border and shadow to separate the panel from desktop content.
- Clear text hierarchy for task content, category, and optional time metadata.
- A more polished Windows-friendly UI font treatment with stronger readability than the current painted text.

Background sampling should not be the primary readability mechanism in this release. It may remain as a future visual enhancement only if it does not affect contrast guarantees.

### Focus List Mode

Focus list mode is the default overview mode.

It should show today's pending tasks in a compact desktop-readable list. Each task row should support the information already relevant to daily work:

- Completion affordance.
- Category.
- Optional time label.
- Task content.

Hover state may reveal richer controls while non-hover state remains calm and readable.

### Active Task Mode

Active task mode is a lightweight execution surface.

It should emphasize:

- The current task.
- Its category and optional metadata.
- The next task hint when available.
- Minimal actions for completing the current task or returning to the list.

This mode should give small positive reinforcement without becoming noisy. Suitable first-release encouragement points are:

- A steady message when a task starts.
- A positive completion message when the active task is finished.

Complex interruption rules, focus analytics, and aggressive reminders are deferred.

### Interaction Model

The sticky overlay should support:

- Moving the panel from its drag area.
- Switching between focus list mode and active task mode.
- Starting a task from the list.
- Completing a task from either relevant mode.
- Adjusting overlay width horizontally.

Width resizing should have minimum and maximum bounds so content does not become unreadable. The chosen width should be restored in later sessions.

## Task Entry Habit Memory

The home page should remember the last selected input time mode:

- No time.
- Time period.
- Precise time.

If the user repeatedly chooses no-time input, reopening the application should preserve that choice instead of resetting to precise-time entry. The first release should use explicit last-used preference memory. History-based inference is deferred unless later evidence shows the explicit memory is insufficient.

## Data And State

### Settings

Add lightweight persisted settings for:

- `task/input_time_mode` for the last selected home-page input mode.
- `sticky/view_mode` for the last sticky display mode when useful.
- `sticky/width` for restored overlay width.

### Active Task Context

The first release needs a lightweight current execution context:

- `active_task_id`.
- `active_started_at`.

This context may live in settings or an equivalent lightweight state mechanism because the first release does not yet need detailed execution history.

### Deferred Execution History

Do not add a full execution-log model in this release solely for future review features. Daily review, focus statistics, and interruption analysis can introduce a dedicated execution history model later when their requirements are concrete.

## Failure Handling

- If active task mode has no current task, show a clear empty-state prompt.
- If the active task is completed or deleted, clear the active task context.
- Existing user databases must keep working after the change.
- Overlay width persistence must clamp invalid stored values to readable bounds.
- The overlay should remain readable on bright, dark, and visually busy desktop backgrounds.

## Scope

### In Scope

- Semi-transparent sticky panel redesign.
- Stable contrast strategy independent of desktop sampling.
- Focus list mode.
- Active task mode.
- Horizontal sticky width resize and persistence.
- Lightweight encouragement around active task flow.
- Last-used home-page input time mode persistence.

### Out Of Scope

- Full daily review workflow.
- Scheduled 21:00 review prompt.
- Dopamine-style review form UI.
- Focus analytics or long-term execution statistics.
- Automated history-based prediction of input time mode.
- Complex reminder cadence and interruption policy.

## Verification Focus

The implementation should verify:

- The sticky overlay stays readable on bright and busy backgrounds.
- The overlay does not flash unreadable text while sampling background colors.
- Width resize works within bounds and restores after restart.
- Switching between focus list mode and active task mode preserves correct task state.
- Completing or deleting the active task clears invalid active context.
- The home-page input time mode restores after reopening the application.
- Existing task data remains usable after schema or setting changes.

## Future Phase

The next phase can close the daily loop with an energetic review flow:

- End-of-work or scheduled nightly review.
- Completed task celebration and unfinished task reflection.
- Category breakdown.
- Lightweight prompts for tomorrow.
- A more colorful, achievement-oriented review form distinct from the quiet sticky overlay.
