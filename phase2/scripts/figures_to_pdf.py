"""Collect phase2/results/final_v3/figures/*.png into one PDF, one figure per page, for the writing chat (HQ 1019)."""
from pathlib import Path
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages

src = Path("phase2/results/final_v3/figures"); files = sorted(src.glob("*.png"))
with PdfPages(src.parent / "figures_final_v3.pdf") as pdf:
    for f in files:
        img = mpimg.imread(f); h, w = img.shape[:2]
        fig = plt.figure(figsize=(11, 11 * h / w + 0.6)); plt.imshow(img); plt.axis("off"); plt.title(f.name, fontsize=10)
        pdf.savefig(fig, dpi=150); plt.close(fig)
print(len(files), "pages")
