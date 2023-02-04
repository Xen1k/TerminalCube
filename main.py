import numpy as np
import os
import time
from abc import ABC, abstractmethod
from copy import copy
from math import cos, sin

def clear(full_clear = False): os.system('cls') if full_clear else print("\033[H\033[J", end='')
SCREEN_SIZE = 90


class Drawable(ABC):
    MAX_DRAWABLE_SIZE = SCREEN_SIZE
    drawcall_matrix = np.zeros((MAX_DRAWABLE_SIZE, MAX_DRAWABLE_SIZE))

    @abstractmethod
    def update_drawcall_matrix(self):
        pass

    @classmethod
    def clear_drawcall_matrix(cls):
        cls.drawcall_matrix = np.zeros((cls.MAX_DRAWABLE_SIZE, cls.MAX_DRAWABLE_SIZE))

    @classmethod
    def display_drawcall_matrix(cls):
        line_string = ''
        display_symbols = { 0: '  ', 1: '▒▒', 2: '██' }
        for i in range(cls.drawcall_matrix.shape[0]):
            for j in range(cls.drawcall_matrix.shape[1]):
                line_string += display_symbols.get(cls.drawcall_matrix[i, j])
            line_string += '\n'
        print(line_string)

class Line(Drawable):

    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2
        self.update_drawcall_matrix()
    
    def get_y_point_on_line(self, x): 
        return (x - self.point1[0]) * (self.point2[1] - self.point1[1]) / (self.point2[0] - self.point1[0]) + self.point1[1]

    def get_x_point_on_line(self, y): 
        return (y - self.point2[1]) / (self.point2[1] - self.point1[1]) * (self.point2[0] - self.point1[0]) + self.point2[0]

    def get_z_point_on_line(self, x): 
        if self.point2[0] - self.point1[0] == 0:
            return 10
        return (x - self.point1[0]) * (self.point2[2] - self.point1[2]) / (self.point2[0] - self.point1[0]) + self.point1[2]

    def update_drawcall_matrix(self):
        min_x = int(min(self.point1[0], self.point2[0]))
        max_x = int(max(self.point1[0], self.point2[0]))
        min_y = int(min(self.point1[1], self.point2[1]))
        max_y = int(max(self.point1[1], self.point2[1]))
        clear_render_z_range = 4
        for i in range(min_x + 1, max_x):
            y_coord = int(self.get_y_point_on_line(i))
            if y_coord < self.MAX_DRAWABLE_SIZE and y_coord >= 0:
                Drawable.drawcall_matrix[y_coord][i] = 1 if self.get_z_point_on_line(i) < clear_render_z_range else 2
        for i in range(min_y + 1, max_y):
            x_coord = int(self.get_x_point_on_line(i))
            if x_coord < self.MAX_DRAWABLE_SIZE and x_coord >= 0:
                Drawable.drawcall_matrix[i][x_coord] = 1 if self.get_z_point_on_line(x_coord) < clear_render_z_range else 2

class Triangle(Drawable):
    def __init__(self, point1, point2, point3):
        self.lines = []
        self.lines.append(Line(point1, point2))
        self.lines.append(Line(point2, point3))
        self.lines.append(Line(point3, point1))

    def set_point(self, point_number, point):
        self.lines[point_number].point1 = self.lines[point_number - 1].point2 = copy(point)

    def get_point(self, point_number):
        return self.lines[point_number].point1

    def update_drawcall_matrix(self):
        for line in self.lines:
            line.update_drawcall_matrix()
        
class Polygon(Drawable):
    def __init__(self, points):
        if len(points) < 3:
            raise Exception("Invalid points, a polygon must have at least 3 vertices")
        
        self.points = points
        self.triangles = []
        self._generate_triangles()

    def _generate_triangles(self):
        for i in range(len(self.points) - 2):
            self.triangles.append(Triangle(self.points[0], self.points[i+1], self.points[i+2]))

    def update_drawcall_matrix(self):
        for triangle in self.triangles:
            triangle.update_drawcall_matrix()

    def set_all_points(self, points):
        self.points = points
        self.triangles = []
        self._generate_triangles()

    def set_point(self, point_number, new_point):
        if point_number >= len(self.points):
            raise Exception("Invalid point, point number is out of range")
        self.points[point_number] = new_point
        self.triangles = []
        self._generate_triangles()

    def get_points(self):
        return self.points

class Mesh(Drawable):
    def __init__(self, mesh_points):
        self.polygons = []
        for polygon_points in mesh_points:
            self.polygons.append(Polygon(polygon_points))
    
    def update_drawcall_matrix(self):
        for polygon in self.polygons:
           polygon.update_drawcall_matrix()
    
    def set_all_points(self, mesh_points):
        for i in range(len(mesh_points)):
            self.polygons[i].set_all_points(mesh_points[i])



def rotate(angle, axis, points):
    rotation_matrices = {
        'x': np.array([[1, 0, 0], [0, cos(angle), -sin(angle)], [0, sin(angle), cos(angle)]]),
        'y': np.array([[cos(angle), 0, sin(angle)], [0, 1, 0], [-sin(angle), 0, cos(angle)]]),
        'z': np.array([[cos(angle), -sin(angle), 0], [sin(angle), cos(angle), 0], [0, 0, 1]])
    }
    rotation_matrix = rotation_matrices[axis]
    return [np.array(point).dot(rotation_matrix).tolist() for point in points]

def translate(translate_vector, points):
    modified_translate_vector = translate_vector.copy()
    modified_translate_vector.append(1)
    translation_matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], modified_translate_vector])
    return [np.array(point + [1]).dot(translation_matrix).tolist()[:-1] for point in points]

def transform_multi(transform_function, points_list):
    return [transform_function(points) for points in points_list]


line_length = 35
cube_coords = [[[0, 0, 0], [line_length, 0, 0], [line_length, line_length, 0], [0, line_length, 0]],
               [[0, 0, 0], [line_length, 0, 0], [line_length, 0, line_length], [0, 0, line_length]],
               [[0, 0, 0], [0, line_length, 0], [0, line_length, line_length], [0, 0, line_length]],
               [[line_length, line_length, line_length], [line_length, 0, 0], [line_length, line_length, 0], [0, line_length, 0]],
               [[line_length, line_length, line_length], [line_length, 0, 0], [line_length, 0, line_length], [0, 0, line_length]],
               [[line_length, line_length, line_length], [0, line_length, 0], [0, line_length, line_length], [0, 0, line_length]]]

cube = Mesh(cube_coords)

center_coords = [30, 30, 0]
cube_coords = transform_multi(lambda points: translate(center_coords, points), cube_coords)

rotation_speed = 0.05


clear(True)
while True:
    Drawable.clear_drawcall_matrix()

    cube_coords = transform_multi(lambda points: rotate(rotation_speed, 'x', points), cube_coords)
    cube_coords = transform_multi(lambda points: rotate(rotation_speed, 'y', points), cube_coords)

    cube.set_all_points(cube_coords)
    cube.update_drawcall_matrix()

    time.sleep(0.005)
    clear()
    Drawable.display_drawcall_matrix()
   
