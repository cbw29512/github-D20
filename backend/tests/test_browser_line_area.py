from pathlib import Path
import subprocess


def test_browser_three_by_two_line_targeting_regression() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["node", str(root / "frontend" / "browser-line-area.test.cjs")],
        cwd=root, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
