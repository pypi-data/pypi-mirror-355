import itertools
import math

class ninjalib:
    def __init__(self,data,a=-1,b=-1,c=-1):
        self.data = data
        self.a = a
        self.b = b
        self.c = c

    def center(self):
        if len(self.data[0]) == 2:
            x = (min([i[0] for i in self.data]) + max([i[0] for i in self.data])) / 2
            y = (min([i[1] for i in self.data]) + max([i[1] for i in self.data])) / 2
            return x,y
        elif len(self.data[0]) == 3:
            x = (min([i[0] for i in self.data]) + max([i[0] for i in self.data])) / 2
            y = (min([i[1] for i in self.data]) + max([i[1] for i in self.data])) / 2
            z = (min([i[2] for i in self.data]) + max([i[2] for i in self.data])) / 2
            return x,y,z
        else:
            x = (min(self.data) + max(self.data)) / 2
            return x
            
    def flatten(self):
        new_data = self.data
        if self.a == -1:
            while True:
                if isinstance(new_data[0],list) or isinstance(new_data[0],tuple):
                    new_data = list(itertools.chain(*new_data))
                else:
                    break
        else:
            for i in range(self.a):
                if isinstance(new_data[0],list) or isinstance(new_data[0],tuple):
                    new_data = list(itertools.chain(*new_data))
        return new_data

    def gravity(self):
        return f"{0.266955e-12 * (self.data / self.a ** 2)} m/s"

    def mean(self):
        return sum(self.data) / len(self.data)

    def project(self):
        if self.c != 0:
            screen_x = math.floor(self.data * (self.a / self.c))
            screen_y = math.floor(self.data * (self.b / self.c))
        else:
            screen_x = self.data + self.a
            screen_y = self.data + self.b
        return [screen_x,screen_y]
