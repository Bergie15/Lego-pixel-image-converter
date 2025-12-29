class VirtualRobot:
    def __init__(self):
        self.x = 0
        self.y = 0

    def move_to(self, x, y):
        print(f"➡️ Move ({self.x},{self.y}) → ({x},{y})")
        self.x, self.y = x, y

    def pick(self, color):
        print(f"🧱 Pick {color}")

    def place(self):
        print("📍 Place brick")
