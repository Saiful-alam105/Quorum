# Quorum Report — Screenshot Checklist

Place real screenshots into `report/screenshots/` using exactly these filenames.
The LaTeX report (`sections/ui_screenshots.tex`) references them; if a file is
missing, the report shows a placeholder box and still compiles.

## Required screenshots

| # | Filename | What to capture | Notes |
|---|----------|-----------------|-------|
| 1 | `01-landing-page.png` | Landing page (public, before login) | Home page hero + sections |
| 2 | `02-github-login.png` | The sign-in transition to GitHub OAuth | Show the "Continue with GitHub" step / GitHub authorize screen |
| 3 | `03-dashboard.png` | Main dashboard | Metrics, "Your Repositories", "Needs attention", recent PRs |
| 4 | `04-repositories.png` | Repositories page | Discovery list with Connected / Needs connection badges |
| 5 | `05-repository-workspace.png` | A connected repository's workspace | PR list + Create PR button |
| 6 | `06-pull-requests.png` | Pull Requests page | PR list with status |
| 7 | `07-pr-review-details.png` | PR review details page | Merge Readiness score, findings, tests, coverage, analysis history |
| 8 | `08-security-findings.png` | Security findings | A finding card with severity, file, line, evidence |
| 9 | `09-test-results.png` | Generated test results | Generated tests with pass/fail outcomes |
| 10 | `10-coverage.png` | Coverage block | Before / after / delta |
| 11 | `11-review-history.png` | Review History page | List of previous analyses with scores |
| 12 | `12-ask-quorum.png` | Ask Quorum page (or floating chat) | A question + grounded answer |
| 13 | `13-settings.png` | Settings page | GitHub account, connected repos, sign out |

## Tips

- Capture at full window size (1920x1080 or wider) so text is readable in print.
- Crop to the relevant area; avoid capturing unrelated tabs.
- Use PNG for clarity.
- If a screen can show two things at once (for example the PR review page shows
  findings, tests, and coverage), a single screenshot is enough — you do not
  need every page twice.

## Optional extra (recommended)

- `14-github-review-comment.png` — the "## Quorum Review" comment that Quorum
  posts on the pull request in GitHub. This demonstrates the GitHub feedback
  loop and is useful for the report, but it is not required.