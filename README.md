# 2d_3_stage_cutting_stock

two-dimensional three-stage cutting stock algorithm

## Code Structure

- `pattern_generator.py`: generate best pattern combinations given items
- `cg.py`: column generation algorithm solve 2d cutting stock problem
- `settings.py`: filepaths of data and results
- `utils`: serval useful classes and functions

## Procedure

1. Generate strips by given items
2. Group plenty of suboptimal segments by dynamic programming algorithm
3. Use column generation algorithm creating patterns which consisted by serval segments
4. Solve optimal pattern combinations by Integer Programming