import _tkinter_pysick as tk
class pysick:
    def __init__(self, width, height):
        self.root = tk.Tk()
        self.root.title('pysick shows')
        self.width = width
        self.height = height
        self.root.geometry(str(self.width) + 'x' + str(self.height))
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height)
        self.canvas.pack()
        self.root.iconbitmap('logo.ico')
    def sickloop(self):
        self.root.mainloop()
    def set_title(self, title):
        self.root.title(title)
    def draw_rect(self, x, y, width, height, fill):
        self.canvas.create_rectangle(x, y, width, height, fill= fill)
    def fill_screen(self, fill):
        self.canvas.create_rectangle(0, 0, self.width,self.height, fill=fill)
    def draw_oval(self, x, y, width, height, fill):
        self.canvas.create_oval(x, y, width, height, fill=fill)
    def draw_circle(self, x, y, radius, fill):
        self.canvas.create_oval(x, y, radius, radius, fill=fill)
    def draw_line(self, x1, y1, x2, y2, fill):
        self.canvas.create_line(x1, y1, x2, y2, fill=fill)
    def is_colliding(self, x1, y1, w1, h1, x2, y2, w2, h2):
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)
    def is_circle_colliding(self, x1, y1, r1, x2, y2, r2):
        dx = x2 - x1
        dy = y2 - y1
        distance_sq = dx * dx + dy * dy  # Avoiding sqrt for efficiency
        return distance_sq < (r1 + r2) * (r1 + r2)
    def lock(self, key, func):
        self.root.bind(key, lambda event: func())
    def unlock(self, key):
        self.root.unbind(key)
    def add_label(self, text, x, y, font=("Arial", 14), color="black"):
        label = tk.Label(self.root, text=text, font=font, fg=color)
        label.place(x=x, y=y)
    def add_button(self, text, x, y, func, width=10, height=2):
        button = tk.Button(self.root, text=text, command=func, width=width, height=height)
        button.place(x=x, y=y)

hello = pysick(1200, 720)
hello.fill_screen('red')
hello.sickloop()

