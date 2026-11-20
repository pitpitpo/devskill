# 📟 Terminal User Interfaces (TUI) Master Architecture (`frameworks/tui/terminal-ui.md`)

> **Standard Identifier**: `FW-FRONTEND-TUI-001`  
> **Frameworks**: Ratatui (Rust), Bubble Tea (Go / Charm), Textual (Python), Ink (React / Node)  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-060**, **R-251**, **R-274**  
> **Last Updated**: 2026-11-20  

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *Terminal User Interfaces are first-class frontend clients. TUIs MUST run non-blocking event loops, render to alternate screen buffers with double-buffered diffing to prevent flicker, handle terminal resizing (`SIGWINCH`) without clipping or panicking, sanitize all external inputs against ANSI escape injection, and guarantee clean cooked-mode terminal restoration on exit or panic.*

---

## 2. Terminal UI Architecture & Double-Buffered Rendering

Modern TUI engines decouple user input, background state changes, and terminal screen redrawing into an event-driven loop.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MODERN TUI ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────┤
│  INPUT EVENT THREAD / CHANNEL (Non-Blocking)                           │
│  • Keyboard (`crossterm::event`, Go `tea.KeyMsg`, Textual events)     │
│  • Mouse Events (Scroll, Click, Drag)                                  │
│  • Window Resize Signals (`SIGWINCH` / `tea.WindowSizeMsg`)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Event Dispatch Channel
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  APPLICATION STATE ENGINE (Elm Architecture / Reducer / Store)         │
│  • Immutable state updates or mutex-guarded models                     │
│  • Background Async Tasks (Tokio / Go routines / Asyncio workers)      │
│  • Emits redraw requests only when state changes                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Model State
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  DOUBLE-BUFFERED TERMINAL RENDERER (Ratatui / Bubble Tea / Textual)    │
│  • Computes next character cell matrix `Buffer(x, y, char, style)`     │
│  • Diffs next buffer against previous buffer                           │
│  • Writes ONLY minimal ANSI escape sequences for changed cells         │
│  • Zero screen flicker, < 16ms render pass, < 1% idle CPU             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Concrete Implementations (Ratatui & Bubble Tea)

### 3.1 Production Ratatui (Rust) Architecture

```rust
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    widgets::{Block, Borders, Paragraph, Row, Table},
    Frame, Terminal,
};
use std::{error::Error, io, time::Duration};

pub struct App {
    pub selected_index: usize,
    pub items: Vec<(String, String, String)>,
    pub should_quit: bool,
}

impl App {
    pub fn new() -> Self {
        Self {
            selected_index: 0,
            items: vec![
                ("SVC-01".into(), "Authentication Service".into(), "HEALTHY".into()),
                ("SVC-02".into(), "Postgres Database Pool".into(), "DEGRADED".into()),
                ("SVC-03".into(), "Redis Caching Layer".into(), "HEALTHY".into()),
            ],
            should_quit: false,
        }
    }

    pub fn on_key(&mut self, key: KeyCode) {
        match key {
            KeyCode::Char('q') | KeyCode::Esc => self.should_quit = true,
            KeyCode::Down | KeyCode::Char('j') => {
                if self.selected_index + 1 < self.items.len() {
                    self.selected_index += 1;
                }
            }
            KeyCode::Up | KeyCode::Char('k') => {
                if self.selected_index > 0 {
                    self.selected_index -= 1;
                }
            }
            _ => {}
        }
    }
}

pub fn run_app<B: Backend>(terminal: &mut Terminal<B>, mut app: App) -> Result<(), Box<dyn Error>> {
    while !app.should_quit {
        terminal.draw(|f| ui(f, &app))?;

        // Non-blocking poll with timeout to prevent CPU busy loops
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                app.on_key(key.code);
            }
        }
    }
    Ok(())
}

fn ui(f: &mut Frame, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Min(0), Constraint::Length(3)])
        .split(f.area());

    let title = Paragraph::new("⚡ DevSkill Production TUI Monitor")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::ALL));
    f.render_widget(title, chunks[0]);

    let rows: Vec<Row> = app.items.iter().enumerate().map(|(idx, (id, name, status))| {
        let style = if idx == app.selected_index {
            Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::White)
        };
        let status_style = if status == "HEALTHY" {
            Style::default().fg(Color::Green)
        } else {
            Style::default().fg(Color::Yellow)
        };
        Row::new(vec![id.clone(), name.clone(), status.clone()])
            .style(style)
    }).collect();

    let table = Table::new(rows, [Constraint::Length(10), Constraint::Min(30), Constraint::Length(12)])
        .header(Row::new(vec!["ID", "Service", "Status"]).style(Style::default().add_modifier(Modifier::UNDERLINED)))
        .block(Block::default().borders(Borders::ALL).title("Service Mesh Status"));
    f.render_widget(table, chunks[1]);

    let footer = Paragraph::new("Press 'j'/'k' or Down/Up to select • 'q' to exit")
        .style(Style::default().fg(Color::DarkGray))
        .block(Block::default().borders(Borders::ALL));
    f.render_widget(footer, chunks[2]);
}
```

### 3.2 Production Bubble Tea (Go) Architecture

```go
package main

import (
	"fmt"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type model struct {
	cursor   int
	choices  []string
	selected map[int]struct{}
	quitting bool
}

func initialModel() model {
	return model{
		choices:  []string{"Run Unit Tests", "Deploy to Staging", "Run Security Scan", "Inspect Logs"},
		selected: make(map[int]struct{}),
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			m.quitting = true
			return m, tea.Quit
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.choices)-1 {
				m.cursor++
			}
		case "enter", " ":
			_, ok := m.selected[m.cursor]
			if ok {
				delete(m.selected, m.cursor)
			} else {
				m.selected[m.cursor] = struct{}{}
			}
		}
	}
	return m, nil
}

func (m model) View() string {
	if m.quitting {
		return "Deployment pipeline cancelled.\n"
	}

	header := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#04B575")).
		Render("Select Pipeline Stages to Execute:\n\n")

	s := header
	for i, choice := range m.choices {
		cursor := " "
		if m.cursor == i {
			cursor = ">"
		}
		checked := " "
		if _, ok := m.selected[i]; ok {
			checked = "x"
		}
		s += fmt.Sprintf("%s [%s] %s\n", cursor, checked, choice)
	}

	s += "\nPress 'q' to quit • 'enter' to toggle\n"
	return s
}
```

---

## 4. Terminal Lifecycle, Raw Mode & Signal Handling

Failing to restore terminal cooked mode on error leaves the user's shell completely broken (invisible cursor, missing carriage returns, scrambled characters). Enforce strict RAII cleanup:

```rust
// src/main.rs - Safe Terminal RAII Hook
use std::panic;

pub fn initialize_terminal() -> Result<Terminal<CrosstermBackend<io::Stdout>>, Box<dyn Error>> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let terminal = Terminal::new(backend)?;

    // Register panic hook to restore cooked terminal mode on panic
    let original_hook = panic::take_hook();
    panic::set_hook(Box::new(move |panic_info| {
        let _ = disable_raw_mode();
        let _ = execute!(io::stdout(), LeaveAlternateScreen, DisableMouseCapture);
        original_hook(panic_info);
    }));

    Ok(terminal)
}

pub fn restore_terminal(mut terminal: Terminal<CrosstermBackend<io::Stdout>>) -> Result<(), Box<dyn Error>> {
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;
    Ok(())
}
```

---

## 5. Security & Performance Considerations

1. **ANSI Escape Code Injection Defense**:
   When displaying external log output, server responses, or untrusted file paths in a TUI, ALWAYS sanitize the text:
   - Malicious escape sequences (`\x1b]50;...\x07`) can manipulate terminal emulator titles, compromise clipboards, or inject keystrokes into the host shell.
   - Strip all non-printable ASCII/C0 control characters (except newline) before buffering:
   ```rust
   pub fn sanitize_terminal_string(input: &str) -> String {
       input.chars().filter(|c| !c.is_control() || *c == '\n' || *c == '\t').collect()
   }
   ```
2. **CPU Utilization & Event Polling**:
   Never write a busy `loop { terminal.draw(...); }` without an event timeout. Yield control to OS polling (`event::poll(Duration::from_millis(50))`) to keep idle CPU usage below **1%**.
3. **Handling High-Frequency Terminal Resizes**:
   When the user drags the terminal window, hundreds of `SIGWINCH` resize events fire. Debounce the resize recalculation or clamp minimum dimensions (e.g. minimum 80 columns by 24 rows) to prevent layout integer overflow panics.

---

## 6. Common Pitfalls & Anti-Patterns

- ❌ **Leaving Terminal in Raw Mode on Crash**: If the application panics without an un-raw cleanup hook, the user's shell becomes unresponsive and unusable. Always use an RAII guard or panic handler.
- ❌ **Unbuffered Printing (`println!`) Inside TUI**: Direct writes to `stdout` bypass the TUI double-buffer, tearing the terminal display and causing jitter. All output must be routed through the widget frame.
- ❌ **Unsanitized Log Ingestion**: Rendering raw server logs directly into a widget allows ANSI escape injection.
- ❌ **Hardcoded Colors Without Monochrome Fallback**: Hardcoding 24-bit TrueColor fails on standard 16-color virtual terminals or SSH sessions.

---

## 7. Verification Checklist

- [ ] Alternate screen buffer entered on startup and cleanly restored on exit.
- [ ] Panic hook registered to disable raw mode and show cursor if an unhandled panic occurs.
- [ ] Event loop uses non-blocking poll with timeout (idle CPU < 1%).
- [ ] Rapid terminal resizing (`SIGWINCH`) tested without panics or layout clipping.
- [ ] External input strings sanitized to prevent ANSI escape injection.
- [ ] Plain text or non-interactive mode (`--plain`) available for accessibility and CI scripting.
