# 回答は日本語で作成してください

# Repository Guidelines

This repository hosts Maidel 2.2, a Windows‑focused Electron + React (TypeScript) frontend with a Python backend powered by Google ADK and MCP tools.

## Project Structure & Module Organization
- `backend/`: Python ADK app entry (`backend/main.py`) and agents in `backend/agents/`.
- `frontend/`: Electron + React UI (`src/`, `public/`); scripts in `package.json`.
- `mcp_tools/calculator/`: Standalone MCP tool (safe calculator) with tests.
- Top‑level scripts/tests: `quick_test.py`, `test_stdio.py`, `simple_test.py`, plus docs (`Maidel 2.2 *.md`).

## Build, Test, and Development Commands
- Backend setup: `pip install -r backend/requirements.txt`
- MCP tool deps: `pip install -r mcp_tools/calculator/requirements.txt`
- Run backend (interactive): `py -m backend.main`
- Run backend (stdio for Electron): `py -m backend.main --stdio`
- Frontend dev: `cd frontend && npm install && npm run dev`
- Frontend build/package: `npm run build` | `npm run dist`
- Smoke tests: `py quick_test.py` | `py test_stdio.py` | `py backend/test_simple.py`
- MCP tool tests: `py -m mcp_tools.calculator.test_calculator`

## Coding Style & Naming Conventions
- Python: PEP 8, 4‑space indents, type hints; modules `snake_case.py`; classes `CamelCase`; functions/vars `snake_case`.
- TypeScript/React: 2‑space indents; components `PascalCase` files in `frontend/src/components/` (e.g., `StatusBar.tsx` + `StatusBar.css`); hooks `useX.ts`.
- Keep sidecar styles `ComponentName.css`. Avoid inline styles for shared UI.

## Testing Guidelines
- Current tests are script‑style runners (no pytest required). Keep new tests under the relevant package and name `test_*.py`.
- For backend message flow, prefer stdio tests (`test_stdio.py`) and unit tests per agent.
- Aim to cover error paths (bad JSON, invalid expressions, timeouts) as in `mcp_tools/calculator/test_calculator.py`.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
- Commits: small, focused, with imperative mood; reference files/areas touched.
- PRs: include description, linked issue(s), run steps, and screenshots/GIFs for UI changes; note backend interface or protocol changes (stdio/MCP).

## Security & Configuration Tips
- Backend loads environment from `.env` (see `backend/main.py`). Do not commit secrets.
- Provide required keys locally via `.env`; use placeholders in examples.
- Validate untrusted input (calculator already sanitizes). Avoid adding `eval`/shell without safeguards.

## Agent‑Specific Notes
- When adding new MCP tools, follow the `mcp_tools/calculator/` layout and expose `tools/list` and `tools/call` handlers with JSON responses.
