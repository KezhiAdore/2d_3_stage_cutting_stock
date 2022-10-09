# 2d_3_stage_cutting_stock

two-dimensional three-stage cutting stock algorithm

## Running

Install requirements

```sh
pip install -r requirements.txt
```

Solving dataset A and dataset B

```sh
python main.py
```

Combining serval patterns to reduce the number of the pictures

```sh
python combine_pattern.py
```

## Code Structure

- `pattern_generator.py`: generate best pattern combinations given items
- `cg.py`: column generation algorithm solve 2d cutting stock problem
- `settings.py`: filepaths of data and results
- `utils`: serval useful classes and functions

## Procedure of Solving A

1. Generate strips by given items
2. Group plenty of suboptimal segments by dynamic programming algorithm
3. Use column generation algorithm creating patterns which consisted by serval segments
4. Solve optimal pattern combinations by Integer Programming

## Procedure of Solving B

1. Divide batches by given data
2. Group items by material for each batch
3. Generate stocking layout by the procedure of solving A