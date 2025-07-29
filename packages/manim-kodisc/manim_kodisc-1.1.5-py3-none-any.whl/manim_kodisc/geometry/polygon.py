from manim import *


class BetterPolygon(Polygon):
    def __init__(self, *vertices, **kwargs):
        self.angles = []
        super().__init__(*vertices, **kwargs)

    def get_points(self, point_labels: list[str] = None, label_size: int = 24) -> VGroup:
        self.points = []

        for i, vertex in enumerate(self.get_vertices()):
            label = point_labels[i] if point_labels and i < len(point_labels) else None
            point = self.get_point(vertex, label, label_size)
            self.points.append(point)
        
        return VGroup(*self.points)

    def get_angles(self, angle_labels: list[str] = None, radius: float = 0.5, label_size: int = 24, label_as_angle=False) -> VGroup:
        self.angles = []

        vertices = self.get_vertices()
        num_vertices = len(vertices)
        for i in range(num_vertices):
            label = angle_labels[i] if angle_labels and i < len(angle_labels) else None
            angle = self.get_angle(i, label, radius, label_size, label_as_angle)
            self.angles.append(angle)
        
        return VGroup(*self.angles)
    
    def get_angle(self, index: int, label: str = None, radius: float = 0.5, label_size: int = 24, label_as_angle=False) -> VGroup:
        vertices = self.get_vertices()
        num_vertices = len(vertices)
        
        p1 = vertices[(index - 1) % num_vertices]
        p2 = vertices[index]
        p3 = vertices[(index + 1) % num_vertices]

        v1 = p1 - p2
        v2 = p3 - p2
        v1_unit = v1 / np.linalg.norm(v1)
        v2_unit = v2 / np.linalg.norm(v2)

        angle1 = np.arctan2(v1[1], v1[0])
        angle2 = np.arctan2(v2[1], v2[0])
        
        interior_angle = (angle2 - angle1) % (2 * PI)
        
        if interior_angle > PI:
            interior_angle = 2 * PI - interior_angle
            angle1, angle2 = angle2, angle1

        is_right_angle = abs(interior_angle - PI/2) < 0.01
        
        angle_marker = VGroup()
        
        if is_right_angle:
            right_angle_size = radius * 0.7
            
            # Calculate points for the right angle marker
            point1 = p2 + right_angle_size * v1_unit
            point2 = p2 + right_angle_size * v2_unit
            corner = p2 + right_angle_size * (v1_unit + v2_unit)
            
            # Create the L-shaped marker
            line1 = Line(point1, corner, color=WHITE)
            line2 = Line(corner, point2, color=WHITE)
            
            angle_marker.add(line1, line2)
        else:
            arc = Arc(
                radius=radius,
                start_angle=angle1,
                angle=interior_angle,
                arc_center=p2,
                color=WHITE
            )
            angle_marker.add(arc)
        
        if label or label_as_angle:
            mid_angle = angle1 + interior_angle / 2
            label_pos = p2 + 1.75 * radius * np.array([
                np.cos(mid_angle),
                np.sin(mid_angle),
                0
            ])

            content = f"{int(np.degrees(interior_angle))}" if label_as_angle else label
            text = MathTex(content, color=self.get_color(), font_size=label_size)
            text.move_to(label_pos)
            angle_marker.add(text)
        
        return angle_marker
    
    def get_side_labels(self, labels: list[str], label_size: int = 24) -> VGroup:
        vertices = self.get_vertices()
        num_vertices = len(vertices)
        
        side_labels = VGroup()
        for i in range(num_vertices):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % num_vertices]
            
            mid_point = (p1 + p2) / 2
            outward_normal = np.array([-(p2[1] - p1[1]), p2[0] - p1[0], 0])
            outward_normal /= np.linalg.norm(outward_normal)
            mid_point -= 0.5 * outward_normal
            
            content = labels[i] if labels and i < len(labels) else f"l_{i}"
            text = MathTex(content, color=self.get_color(), font_size=label_size)
            text.move_to(mid_point)
            side_labels.add(text)
        
        return side_labels
    
    def get_start_angle(self, p1: np.ndarray, p2: np.ndarray) -> tuple[int, int]:
        v1 = p1 - p2
        return np.arctan2(v1[1], v1[0])