from circleshape import CircleShape
from constants import Shot_RADIUS


class Shot(CircleShape):
    def __init__(self, position, velocity):
        super().__init__(position, Shot_RADIUS)
        self.velocity = velocity
