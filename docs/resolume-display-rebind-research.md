# Resolume Advanced Output — Remote Trigger Research

**Problem.** After an overnight projector power-cycle, Windows shuffles display IDs. Arena's existing screen→display mapping breaks and walls go black. The manual fix is one click: *Output → Advanced Output* in Arena's menu. Opening the panel makes Arena re-enumerate displays and re-bind its outputs. We want to trigger this remotely so Blair / the docent don't need to do it.

Three paths were considered. First two are eliminated; third is the remaining candidate.

---

## Path 1 — SendKeys / hotkey (tried 2026-04-16, failed)

Scripted Ctrl+Shift+A from a hidden PowerShell scheduled task.

**Outcome.** Dead end. Windows foreground-lock prevents a background task from stealing focus. The console briefly flashes but keystrokes never reach Arena. Confirmed by Prav on live call — panel did not open.

## Path 2 — REST / OSC (tried 2026-04-16 OSC; researched REST 2026-04-16, both dead ends)

### OSC

Sent `/composition/screens/{n}/bypassed` toggles. Arena's OSC log panel confirms messages arrive. Walls *blink* (proving plumbing), but bypass toggles operate at the signal level — they do not trigger Arena's display enumeration routine. When the display IDs have shuffled, bypass toggles do nothing useful.

### REST API (conclusive finding from spec review)

Arena exposes a REST API on `http://localhost:8080/api/v1` *when enabled in Preferences → Webserver*. Spec: `https://resolume.com/docs/restapi/swagger.yaml` (OpenAPI 3.0.1, 149 paths).

Inventoried every path in the spec:

- `composition`, `column`, `layer`, `layergroup`, `deck`, `clip` — full CRUD on the composition hierarchy.
- `effects`, `sources`, `files`, `api` — metadata retrieval.
- `/parameter/by-id/{parameter-id}` — generic get/set for any knob by its internal parameter ID.
- `/composition/action` — *only undo / redo*.
- `/composition/open` — reload a composition from file.
- `/composition/disconnect-all` — disconnect all clips.

**Zero endpoints expose "screens", "displays", "outputs", or the Advanced Output panel.** The word "display" appears only in `set-display-name` (renaming effects).

Because every OSC screen parameter (`/composition/screens/N/bypassed`) has a corresponding internal parameter ID, we could in principle address screens via `/parameter/by-id/...` — but that is the *same parameter system* OSC already exposed, and bypass toggles there already proved insufficient (Path 2 OSC above). REST gives us no new primitives.

**Nuclear option**: `POST /composition/open` with the currently-loaded composition path forces Arena to re-read everything from disk, which would re-initialise outputs as a side effect. Downside: it disconnects every clip and effectively restarts the show mid-visitor. Unacceptable during gallery hours.

**Verdict.** REST API is the wrong level of the stack for this problem. The Advanced Output panel performs a UI-triggered internal routine (display enumeration + output rebind) that is not exposed as a parameter or action in the public API.

**Side-observation from 3090 probe** (2026-04-16): Arena webserver is *not* currently listening on port 8080 on the 3090 — the feature must be enabled in Preferences by Prav before any REST path could be tested anyway. Worth enabling for future composition-level automation, but it doesn't change the conclusion above.

## Path 3 — Windows UI Automation (working, 2026-04-16)

Windows exposes every application's UI tree via the UI Automation framework (`System.Windows.Automation` in PowerShell). Screen readers use it to click menu items *without stealing foreground focus* — the click is invoked through the accessibility layer, not simulated keystrokes.

**Result: end-to-end invocation of `Output → Advanced...` succeeded remotely via SSH → scheduled task → UIA.** Full script at `scripts/resolume_rebind_uia.ps1`.

### What worked

1. Arena's JUCE UI *does* publish its menu bar to UIA. The initial probe (`scripts/resolume_uia_probe.ps1`) found all 10 top-level items: `Arena, Composition, Deck, Group, Layer, Column, Clip, Output, Shortcuts, View`.
2. Top-level items advertise `InvokePattern`, not `ExpandCollapsePattern` — JUCE treats them as invokable buttons. `Invoke()` opens the dropdown.
3. The dropdown's submenu items live in a popup window *parented to the desktop*, not to Arena's main window. Must search `AutomationElement.RootElement` after invoke, not `Arena`'s root.
4. The menu item is named `Advanced...` (with ellipsis), not `Advanced Output`. After invoking `Output`, the full submenu is enumerable and includes a rich list of display controls:

   ```
   Fullscreen → Display 1 (1920x1080), Display 2 (1920x1080), Display 3 (1920x1080), Display 4 (1680x1050)
   Windowed   → Display 1..4 (same resolutions)
   Advanced...
   Composition output sharing
   Texture sharing (Spout)
   Network streaming (NDI)
   Identify Displays
   Open System Display Preferences
   Show FPS / Show Test Card / Show Display Info / Snapshot
   ```

   Display resolutions themselves are observable via UIA — confirms Windows is currently seeing all four projectors and reporting correct resolutions. Display 4 (back wall) is 1680x1050; others are 1920x1080.

### What was learned the hard way

- **`MainWindowHandle = 0` from SSH.** SSH spawns a service-session process; Arena's window lives in the interactive console session. `Get-Process Arena` returns the process but `MainWindowHandle` is 0 from outside the session. Fix: run the script from a **scheduled task registered with `/it /ru user`** (the same pattern already used by `SSD-Resolume-Kick`). SSH triggers the task; the task runs in the console session and *does* see the window handle.
- **Menu tree is focus-dependent.** If Arena doesn't have focus, its menu bar children may not appear under the root `AutomationElement`. The first live invocation showed `0 MenuItems visible` after `Output` was invoked — the fix was to search from `RootElement` rather than Arena's window element, because the popup is a desktop-level window.
- **Name matters exactly.** Searching for `Advanced Output` returned nothing; the actual `Name` is `Advanced...`. Always dump the tree to confirm names rather than guessing from the visual label.

### Remote trigger

```bash
ssh windows-desktop-remote "schtasks /run /tn SSD-Resolume-Rebind-UIA"
```

The task is registered on the 3090 (one-time schedule `2099-12-31 23:59`, interactive, run-as `user`, highest integrity). SSH fires it; the task runs the PowerShell script in the console session; logs to `C:\Users\user\resolume_rebind_uia.log`.

### What's still unproven

**The semantic test.** We've confirmed Arena receives the menu invocation. We have *not* yet confirmed this recovers walls from the actual "display-ID shuffled after projector power cycle" state, because when the script was run the system was already healthy. That test needs to happen with Prav:

1. Power-cycle projectors to induce the display shuffle (walls go dark).
2. Fire `ssh windows-desktop-remote "schtasks /run /tn SSD-Resolume-Rebind-UIA"`.
3. Observe whether walls recover within ~10 seconds (same timing as Prav's manual click).

Scheduled for the Saturday cold-boot validation session with Prav, alongside EDID dongle install.

### Side finding: per-display Fullscreen toggles are also addressable

Because each `Fullscreen → Display N` entry is a regular `MenuItem` invocable via UIA, we have a finer-grained recovery path than just opening Advanced Output: we can programmatically toggle fullscreen on any individual display. Useful if (for example) only one wall is dark — avoids disrupting the three healthy walls.

Not wired up yet; noted as an option for targeted recovery in a future revision.

---

## Summary for project docs

| Path | Verdict | Reason |
|---|---|---|
| SendKeys hotkey | Dead end | Windows foreground-lock |
| OSC `screens/bypassed` | Dead end | Wrong stack level — signal, not topology |
| REST API | Dead end | No display/screen/output endpoints exist; same parameter system as OSC |
| **UIAutomation** | **Working** | End-to-end invocation verified 2026-04-16; semantic recovery test pending Saturday |
| EDID dongles (parallel) | Hardware fix | Stabilises display IDs so the problem doesn't arise; installed Saturday |

EDID dongles are the real long-term fix — they prevent the display shuffle from happening. UIA is the belt-and-braces software guardrail that runs regardless. Use both.
