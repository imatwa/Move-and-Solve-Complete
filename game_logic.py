class ScoreCounter:
    def __init__(self):
        self.score = 0
        self.last_jumps = 0
        self.last_squats = 0
        self.last_bends = 0

    def update(self, jumps, squats, bends):
        if jumps > self.last_jumps:
            self.score += (jumps - self.last_jumps) * 1
            self.last_jumps = jumps

        if bends > self.last_bends:
            self.score += (bends - self.last_bends) * 5
            self.last_bends = bends

        if squats > self.last_squats:
            self.score += (squats - self.last_squats) * 10
            self.last_squats = squats

        return self.score

    def reset(self):
        self.score = 0
        self.last_jumps = 0
        self.last_squats = 0
        self.last_bends = 0
