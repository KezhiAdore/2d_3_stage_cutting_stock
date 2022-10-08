from matplotlib import pyplot as plt
from matplotlib import patches
from matplotlib import lines
import dill

def gen_remnant(x,y,width,height):
    remnant=patches.Rectangle(
        (x,y),
        width=width,
        height=height,
        hatch="/",
        fill=True,
        color=(0.8,0.8,0.8)
    )
    return remnant

def gen_rect(x,y,width,height,color,linewidth=1):
    rect=lines.Line2D(
        xdata=[x,x,x+width,x+width,x],
        ydata=[y,y+height,y+height,y,y],
        color=color,
        linewidth=linewidth,
    )
    return rect

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
            rect = gen_rect(left+i*self._l,bottom,self._l,self._w,(0/255,90/255,171/255))
            ax.add_line(rect)
        # plot remnant
        left=left+self._e*self._l
        if left<self._x:
            remnant=gen_remnant(left,bottom,self._x-left,self._w)
            ax.add_patch(remnant)
            
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
    def __init__(self, x, W, strips) -> None:
        self._x = x
        self._W = W
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
        # plot strips
        bottom = 0
        for strip in self._strips:
            strip.plot(ax, left, bottom)
            bottom += strip.w
        
        # plot 2nd cutting line
        bottom=0
        for strip in self._strips:
            bottom += strip.w
            cut_line=lines.Line2D(
                    xdata=[left,left+strip.x],
                    ydata=[bottom,bottom],
                    linewidth=1,
                    color=(0,1,0)   # green
                )
            ax.add_line(cut_line)
        
        # plot remnant
        if bottom<self._W:
            remnant=gen_remnant(left,bottom,self._x,self._W-bottom)
            ax.add_patch(remnant)
    
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
        # plot segments
        left = 0
        for segment in self._segments:
            segment.plot(ax, left)
            left += segment.x
        
        # plot 1st cutting line
        left = 0
        for segment in self._segments:
            left += segment.x
            cut_line=lines.Line2D(
                xdata=[left,left],
                ydata=[0,self._W],
                linewidth=1,
                color=(1,0,0)   # red
            )
            ax.add_line(cut_line)
        
        # plot remnant
        if left<self._L:
            remnant=gen_remnant(left,0,self._L-left,self._W)
            ax.add_patch(remnant)
        
        # plot plate
        rect=gen_rect(0,0,self._L,self._W,(0,0,0))
        ax.add_line(rect)
    
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
