"""Shared paths and helpers of the signal-region plot scripts (SignalRegion/python/plot*.py).

Inputs are the local copies of the SignalRegionStudy products (submodule SignalRegionStudy/,
results/ in git; templates synced to SKNanoOutput/SignalRegionStudy/). Plots go to
SignalRegion/plots/<AN|PW>/2024/<category>/, written as png and pdf (style an) or pdf (style pw).
No numbers are produced here except the printed tables; the SignalRegionStudy submodule keeps
no plotting code.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRS = REPO / "SignalRegionStudy"
sys.path.insert(0, str(REPO / "Common" / "Tools"))
sys.path.insert(0, str(SRS / "python"))
import plotter  # noqa: E402

ERA = "2024"
MHC = 130
GRID_MA = list(range(15, 130, 5))   # configs/masspoints.json: MHc130_MA15-125, 5 GeV
TEMPLATES = REPO / "SKNanoOutput" / "SignalRegionStudy" / ERA / "HcToWABTagEff_v2" / "templates"   # v2 = v1 with lumi_2024 1.016 (shapes identical)
PREV = REPO / "docs" / "previous_analysis" / "ChargedHiggsAnalysisV3" / "SignalRegionStudyV4"

CH_LABEL = {"Combined": "e#mu#mu + #mu#mu#mu", "SR1E2Mu": "e#mu#mu", "SR3Mu": "#mu#mu#mu",
            "SR3Mu_lowM": "#mu#mu#mu, lower-mass pair", "SR3Mu_highM": "#mu#mu#mu, higher-mass pair"}
MA_TITLE = "m_{A} [GeV]"


def masspoint(ma, mhc=MHC):
    return f"MHc{mhc}_MA{ma}"


def outdir(style, category):
    d = plotter.plot_dir("SignalRegion", style, ERA) / category
    d.mkdir(parents=True, exist_ok=True)
    return d


def save(canvas, style, category, name):
    """Write <name>.png and <name>.pdf (an) or <name>.pdf (pw); returns the paths."""
    d = outdir(style, category)
    paths = [d / f"{name}.pdf"] if style == "pw" else [d / f"{name}.pdf", d / f"{name}.png"]
    for p in paths[:-1]:
        canvas.canv.SaveAs(str(p))
    plotter.save(canvas.canv, paths[-1])   # last format closes the canvas
    return paths
