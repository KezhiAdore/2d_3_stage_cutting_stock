from matplotlib import pyplot as plt
from matplotlib import patches
import dill


class Strip:
    def __init__(self, x, l, w, e, v) -> None:
        """_summary_

        Args:
            x (float): length of the strip
            l (float): length of the item which consists the strip
            w (float): width of the item which consists the strip
            e (float): max number of items in the strip
            v (float): value of the strip
        """
        self._x = x
        self._l = l
        self._w = w
        self._e = e
        self._v = v

    def __str__(self) -> str:
        return f"x: {self._x}, l:{self._l}, w:{self._w}, e:{self._e}, v:{self._v}"

    def plot(self, ax, left, bottom):
        for i in range(self.e):
            rect = patches.Rectangle(
                (left+i*self._l, bottom),
                width=self._l,
                height=self._w,
                fill=False
            )
            ax.add_patch(rect)
            print
        plt.plot()

    @property
    def x(self):
        return self._x

    @property
    def l(self):
        return self._l

    @property
    def w(self):
        return self._w

    @property
    def e(self):
        return self._e

    @property
    def v(self):
        return self._v


class Segment:
    def __init__(self, x, strips) -> None:
        self._x = x
        self._strips = strips

    def __str__(self) -> str:
        s = ""
        for strip in self._strips:
            s += str(strip)+"\n"
        return s

    def append(self, strip):
        self._strips.append(strip)

    def plot(self, ax, left=0):
        bottom = 0
        for strip in self._strips:
            strip.plot(ax, left, bottom)
            bottom += strip.w

    def item_amount(self, length, width):
        """amount of item whose length and width is given

        Args:
            length (float): length of the item
            width (float): width of the item

        Returns:
            amount: int, number of the item
        """
        amount = 0
        for strip in self._strips:
            if strip.l == length and strip.w == width:
                amount += strip.e
        return amount

    @property
    def x(self):
        return self._x

    @property
    def strips(self):
        return self._strips

    @property
    def v(self):
        v = 0
        for strip in self._strips:
            v += strip.v
        return v

    @property
    def empty(self):
        return not self._strips


class Pattern:
    def __init__(self, segments) -> None:
        self._segments = segments

    def __str__(self) -> str:
        s = ""
        for segment in self._segments:
            s += segment+"\n"
        return s

    def plot(self, ax):
        left = 0
        for segment in self._segments:
            segment.plot(ax, left)
            left += segment.x


def dill_load(path):
    with open(path, "rb") as f:
        obj = dill.load(f)
        f.close()
    return obj


def dill_save(obj, path):
    with open(path, "wb") as f:
        dill.dump(obj, f)
        f.close()


if __name__ == "__main__":
    strip = Strip(50, 10, 20, 2, 200)
    seg = Segment(1, [strip, strip, strip])
    fig, ax = plt.subplots()
    seg.plot(ax, 0)
    plt.show()
