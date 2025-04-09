"""
<<<
2
4
5 5
5 -5
-5 5
-5 -5
2
-100000 -100000
100000 100000

>>>
0.000000000000
282842.712474619038

<<<
1
10
26 -76
65 -83
78 38
92 22
-60 -42
-27 85
42 46
-86 98
92 -47
-41 38

>>>
13.341664064126334
"""

import typing

from decimal import Decimal


class  Point2D:
    x: int
    y: int

    def __init__(self, x: int, y: int, ):
        self.x = x
        self.y = y

    def __add__(self, other: "Point2D", ):
        return Point2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: "Point2D", ):
        return Point2D(self.x - other.x, self.y - other.y)

    def __mul__(self, s: int):
        return Point2D(self.x * s, self.y * s)

    def __rmul__(self, s: int):
        return Point2D(self.x * s, self.y * s)

    def __repr__(self,):
        return str(self)

    def __str__(self,):
        return f"({self.x}, {self.y})"
    
    @property
    def scale(self,):
        x = Decimal(self.x)
        y = Decimal(self.y)
        return float((x ** 2 + y ** 2).sqrt())

def sum_vectors_by_points(vectors: typing.List[Point2D]) -> Point2D:
    if len(vectors) % 2 != 0:
        return None
    else:
        print(f"{vectors=}")
        pzero = Point2D(0,0)
        for idx in range(len(vectors)):
            print(f"{pzero}")
            if idx % 2 == 0: 
                pzero = pzero + vectors[idx]
            else:
                pzero = pzero + vectors[idx] * (-1)
        return pzero

def reverse_inside(arr, i, j):
    return arr[:i] + arr[i:j+1][::-1] + arr[j+1:]

def get_min_vector_scale(vectors):
    min_scale = sum_vectors_by_points(vectors).scale
    print(f"{min_scale=}")

    for i in range(len(vectors)):
        for j in range(i+1, len(vectors)):
            vec = sum_vectors_by_points(
                reverse_inside(vectors, i, j)
                )
            scale = vec.scale
            print(f"{vec=}, {scale=}")
            if min_scale > scale:
                min_scale = scale

    return min_scale 

def main():
    num_cases = int(input())

    while num_cases > 0:
        num_vectors = int(input())
        vectors: typing.List[Point2D] = []

        while num_vectors:
            a, b, *_ = map(int, input().split())

            vectors.append(Point2D(a, b))
            
            num_vectors -= 1

            print(get_min_vector_scale(vectors))
        
        num_cases -= 1
    

if __name__ == "__main__":
    # vs=[(26, -76), (65, -83), (78, 38), (92, 22), (-60, -42), (-27, 85), (42, 46), (-86, 98), (-41, 38), (92, -47)]
    # vs = [(26, -76), (65, -83), (78, 38), (92, 22), (-60, -42), (-27, 85), (42, 46), (-86, 98), (92, -47), (-41, 38)]
    # vecs = []
    # for v in vs:
        # vecs.append(Point2D(*v))

    # vecs = [Point2D(-100000, -100000), Point2D(100000, 100000)]
    # vecs = [
    #     Point2D(5,5),
    #     Point2D(-5,5),
    #     Point2D(5,-5),
    #     Point2D(-5,-5),
    # ]
    # s = get_min_vector_scale(vecs)
    # print(s)
    # main()

    print(Point2D(1,2) + Point2D(3,4))
