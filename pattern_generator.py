import copy
import math
import os
import dill
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from multiprocessing import Pool

from settings import dataA_paths, dataB_paths, segments_path, segment_figures_dir
from utils import Strip, Segment, dill_load, dill_save
import settings

for name, value in settings.__dict__.items():
    if "dir" in name:
        dir_path = value
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


class PatternGenerator:

    def __init__(self, df: pd.DataFrame, L, W) -> None:
        self._origin_df = df
        self._item_shape = []
        self._item_require_num = {}
        self._item_product_num = {}
        self.init_item()

        self._L = L   # 原料版长度
        self._W = W   # 原料板宽度
        self._interval = 1

        self._q = self.q_set()
        self._strips = self.generate_strips()

        self._segments = []
        self.repeat_generate_segments()

    def init_item(self):
        for _, row in self._origin_df.iterrows():
            item_length = row["item_length"]
            item_width = row["item_width"]

            self._item_shape.append((item_length, item_width))
            self._item_shape.append((item_width, item_length))

            if item_length not in self._item_require_num.keys():
                self._item_require_num[item_length] = {}
            if item_width not in self._item_require_num[item_length].keys():
                self._item_require_num[item_length][item_width] = 1
            else:
                self._item_require_num[item_length][item_width] += 1

        # item去重
        self._item_shape = list(set(self._item_shape))

    def item_require_num(self, length, width):
        if length in self._item_require_num.keys():
            if width in self._item_require_num[length].keys():
                return self._item_require_num[length][width]

        if width in self._item_require_num.keys():
            if length in self._item_require_num[width].keys():
                return self._item_require_num[width][length]
        raise ValueError(
            "can not find length={},width={} in item list".format(length, width))

    def reduce_item_require(self, length, width, reduce_num=1):
        if length in self._item_require_num.keys():
            if width in self._item_require_num[length].keys():
                if self._item_require_num[length][width] >= 0:
                    self._item_require_num[length][width] = max(
                        self._item_require_num[length][width]-reduce_num, 0)
                    return
                else:
                    raise ValueError(
                        self._item_require_num[length][width], "should larger than 0")

        if width in self._item_require_num.keys():
            if length in self._item_require_num[width].keys():
                if self._item_require_num[width][length] >= 0:
                    self._item_require_num[width][length] = max(
                        self._item_require_num[width][length]-reduce_num, 0)
                    return
                else:
                    raise ValueError(
                        self._item_require_num[width][length], "should larger than 0")

        raise ValueError(
            "can not find length={},width={} in item list".format(length, width))

    def item_product_num(self, length, width):
        if length in self._item_require_num.keys() and width in self._item_require_num[length].keys():
            if length not in self._item_product_num.keys():
                self._item_product_num[length] = {}
                if width not in self._item_product_num[length].keys():
                    self._item_product_num[length][width] = 0
            return self._item_product_num[length][width]

        if width in self._item_require_num.keys() and length in self._item_require_num[width].keys():
            if width not in self._item_product_num.keys():
                self._item_product_num[width] = {}
                if length not in self._item_product_num[width].keys():
                    self._item_product_num[width][length] = 0
            return self._item_product_num[width][length]
        raise ValueError(
            "can not find length={},width={} in item list".format(length, width))

    def q_set(self):
        q = [self._L]
        for shape in self._item_shape:
            item_length = shape[0]
            item_width = shape[1]
            for k in range(min(self.item_require_num(item_length, item_width), int(self._L/item_length))+1):
                q.append(k*item_length)
        q = list(set(q))
        q.sort()
        return q

    def generate_strips(self):
        strips = {}
        for x in self._q:
            strips[x] = []
            for shape in self._item_shape:
                item_length = shape[0]
                item_width = shape[1]
                if item_length > x:
                    continue
                item_value = item_length*item_width
                e_max = min(int(x/item_length),
                            self.item_require_num(item_length, item_width))
                strips[x].append(
                    Strip(x, item_length, item_width, e_max, item_value))
        return strips

    def repeat_generate_segments(self):
        if os.path.exists(segments_path):
            self._segments = dill_load(segments_path)
        while not self.check_segments_coverage():
            self.reduce_require_item_from_segments()
            self._segments.extend(self.generate_segments())
        dill_save(self._segments, segments_path)
        return self._segments

    def generate_segments(self):

        segments = []
        with Pool(processes=8) as pool:
            results = pool.map(self.generate_segment_x, [
                               x for x in self._strips])

        for i, r in enumerate(results):
            if not r.empty:
                segments.append(r)

        return segments

    def generate_segment_x(self, x):
        print("generate segment x: {}".format(x))
        strips = self._strips[x]
        # initial dp function
        dp_F = {}
        dp_n = {}
        dp_segment = {}
        dp_F[0] = 0
        dp_segment[0] = Segment(x, [])
        for length in self._item_require_num.keys():
            dp_n[length] = {}
            for width in self._item_require_num[length].keys():
                dp_n[length][width] = {}
                dp_n[length][width][0] = 0

        for y in np.arange(self._interval, self._W+self._interval, self._interval):
            max_F = 0
            max_strip = None
            max_e = 0
            for strip in strips:
                item_width = strip.w
                if math.ceil(item_width) > y:
                    continue
                item_length = strip.l
                if item_length in self._item_require_num.keys() and item_width in self._item_require_num[item_length].keys():
                    n = dp_n[item_length][item_width][y-math.ceil(item_width)]
                elif item_width in self._item_require_num.keys() and item_length in self._item_require_num[item_width].keys():
                    n = dp_n[item_width][item_length][y-math.ceil(item_width)]
                else:
                    raise ValueError(
                        "can not find length={},width={} in item list".format(length, width))
                e_max = min(int(x/item_length), strip.e-n)
                value = strip.v
                new_F = dp_F[y-math.ceil(item_width)]+e_max*value
                if new_F > max_F:
                    max_F = copy.deepcopy(new_F)
                    max_strip = copy.deepcopy(strip)
                    max_e = copy.deepcopy(e_max)

            if dp_F[y-self._interval] >= max_F:
                dp_F[y] = dp_F[y-self._interval]
                dp_segment[y] = copy.deepcopy(dp_segment[y-self._interval])
                for length in self._item_require_num.keys():
                    for width in self._item_require_num[length].keys():
                        dp_n[length][width][y] = dp_n[length][width][y-self._interval]
            else:
                item_width = max_strip.w
                item_length = max_strip.l
                dp_F[y] = max_F
                dp_segment[y] = copy.deepcopy(
                    dp_segment[y-math.ceil(item_width)])
                dp_segment[y].append(
                    Strip(x, item_length, item_width, max_e, max_strip.v))
                for length in self._item_require_num.keys():
                    for width in self._item_require_num[length].keys():
                        dp_n[length][width][y] = dp_n[length][width][y -
                                                                     math.ceil(item_width)]
                if item_length == item_width:
                    dp_n[item_length][item_width][y] += max_e
                elif item_length in self._item_require_num.keys() and item_width in self._item_require_num[item_length].keys():
                    dp_n[item_length][item_width][y] += max_e
                elif item_width in self._item_require_num.keys() and item_length in self._item_require_num[item_width].keys():
                    dp_n[item_width][item_length][y] += max_e
                else:
                    raise ValueError(
                        "can not find length={},width={} in item list".format(length, width))

        best_segment = dp_segment[self._W]
        print("generate segment x: {} complete".format(x))

        return best_segment

    def export_segment_figures(self):
        for i, segment in enumerate(self._segments):
            plt.clf()
            plt.cla()
            fig, ax = plt.subplots()
            segment.plot(ax)
            plt.plot()
            figure_path = os.path.join(
                segment_figures_dir, "{}_{}.png".format(i, segment.x))
            plt.savefig(figure_path)

    def segments_item_amount(self, item_length, item_width):
        """computing the number of the given item in current segments

        Args:
            item_length (float): length of the given item
            item_width (float): width of the given item

        Returns:
            item_amount: an integer representing the number of the given item
        """
        item_amount = sum(
            [
                seg.item_amount(item_length, item_width) +
                seg.item_amount(item_width, item_length)
                for seg in self._segments
            ]
        )
        return item_amount

    def check_segments_coverage(self):
        """check if the current segments cover all the item type

        Returns:
            bool: True means the current segments have covered all the item type,
            False means there exists item type which has not been covered
        """
        for _, row in self._origin_df.iterrows():
            item_length = row["item_length"]
            item_width = row["item_width"]
            item_amount = self.segments_item_amount(item_length, item_width)
            if item_amount == 0:
                # print("item whose length is {} and width is {} is not covered".format(item_length,item_width))
                return False
        return True

    def reduce_require_item_from_segments(self):
        for seg in self._segments:
            for strip in seg.strips:
                self.reduce_item_require(strip.l, strip.w, strip.e)

    def generate_pattern(self):
        pass


if __name__ == "__main__":
    df = pd.read_csv(dataA_paths[0])
    pg = PatternGenerator(df, L=2440, W=1220)
    print(len(pg._item_require_num))
    print(len(pg._item_shape))
    print(len(pg._q))
    pg.check_segment_coverage()
    pg.export_segment_figures()
    pg.generate_segment_x(2440)

    # print(pg.df.sort_values(by=["item_length","item_width"]))
    # print(pg.df.describe())