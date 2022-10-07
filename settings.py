import os

dataA_dir = "data/子问题1-数据集A/"
dataB_dir = "data/子问题2-数据集B/"

dataA_paths = [
    os.path.join(dataA_dir, f"dataA{i}.csv") for i in range(1, 5)
]

dataB_paths = [
    os.path.join(dataB_dir, f"dataB{i}.csv") for i in range(1, 6)
]

results_dir = "results"
segments_path = os.path.join(results_dir, "segments.pkl")

figures_dir = os.path.join(results_dir, "figures")
segment_figures_dir = os.path.join(figures_dir, "segments")
