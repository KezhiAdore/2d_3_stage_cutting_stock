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
        plt.plot()
    
    def to_rows(self,material,plate_id,left,bottom):
        rows=[]
        for i in range(self.e):
            row={
                "material":material,
                "plate_id":plate_id,
                "item_id":None,
                "left":left+i*self._l,
                "bottom":bottom,
                "item_length":self._l,
                "item_width":self._w,
            }
            rows.append(row)
        return rows
    
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o,self.__class__):
            return self.__dict__==__o.__dict__
        return False
    
    def __hash__(self) -> int:
        return hash((
            self._x,
            self._l,
            self._w,
            self._e,
            self._v
        ))
            
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
    
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o,self.__class__):
            return self.__dict__==__o.__dict__
        return False
    
    def __hash__(self) -> int:
        return hash(tuple(self._strips))
    
    def append(self, strip):
        self._strips.append(strip)

    def plot(self, ax, left=0):
        bottom = 0
        for strip in self._strips:
            strip.plot(ax, left, bottom)
            bottom += strip.w
    
    def to_rows(self,material,plate_id,left):
        bottom = 0
        rows=[]
        for strip in self._strips:
            rows.extend(strip.to_rows(material,plate_id,left,bottom))
            bottom += strip.w
        return rows

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
    def __init__(self, segments, use_num, L, W, material) -> None:
        self._segments = segments
        self._use_num=use_num
        self._L = L
        self._W = W
        self._material=material

    def __str__(self) -> str:
        s = ""
        for segment in self._segments:
            s += segment+"\n"
        return s
    
    def append(self, segment):
        self._segments.append(segment)

    def plot(self, ax):
        rect = patches.Rectangle(
                (0, 0),
                width=self._L,
                height=self._W,
                fill=False,
                edgecolor=(0,1,0)
            )
        ax.add_patch(rect)
        left = 0
        for segment in self._segments:
            segment.plot(ax, left)
            left += segment.x
    
    def to_rows(self,plate_id):
        left = 0
        rows=[]
        for segment in self._segments:
            rows.extend(segment.to_rows(self._material,plate_id,left))
            left += segment.x
        return rows
    
    @property
    def use_num(self):
        return self._use_num
    
    @property
    def length(self):
        return sum([seg.x for seg in self._segments])


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
