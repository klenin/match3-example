from pygame.math import Vector2
from enum import Enum
import random as rnd
import math
import copy
import json
import datetime

class CellType:
    EMPTY = 0
    RUBY = 1
    EMERALD = 2
    DIAMOND = 3
    AMBER = 4
    BERYL = 5
    NORMAL_SET = [RUBY, EMERALD, DIAMOND, AMBER, BERYL]

def v2int(v): return int(v.x), int(v.y)

class History:
    def __init__(self, name, field, level):
        self.name = name
        self.field = copy.deepcopy(field)
        self.moves = []
        self.times = []
        self.level = level

    def save(self):
        d = datetime.datetime.now()
        ds = d.strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"log/{self.name}_{ds}.log", "w") as f:
            json.dump({
                'name': self.name,
                'level': self.level,
                'candidates': self.field.candidates,
                'field': self.field.cells,
                'moves': self.moves,
                'times': self.times,
            }, f)

    @staticmethod
    def load_field(level, filename):
        with open(f"log/{filename}.log") as f:
            j = json.load(f)
            return Field(level, rnd.Random(), candidates=j['candidates'])

class Level:
    def __init__(self, name, prob):
        self.name = name
        self.prob = prob

LEVELS = [
    Level("L1", {
        CellType.RUBY: 5,
        CellType.EMERALD: 4,
        CellType.DIAMOND: 1,
        CellType.AMBER: 1,
        CellType.BERYL: 0,
    }),
    Level("L2", {
        CellType.RUBY: 1,
        CellType.EMERALD: 1,
        CellType.DIAMOND: 1,
        CellType.AMBER: 1,
        CellType.BERYL: 0,
    }),
    Level("L3", {
        CellType.RUBY: 1,
        CellType.EMERALD: 1,
        CellType.DIAMOND: 1,
        CellType.AMBER: 1,
        CellType.BERYL: 1,
    }),
]

class Field:
    SIZE = 9
    MIN_EXPLODE = 3
    COST = {
        CellType.RUBY: 5,
        CellType.EMERALD: 4,
        CellType.DIAMOND: 3,
        CellType.AMBER: 2,
        CellType.BERYL: 1,
    }

    def __init__(self, level, rnd, candidates=None):
        self.score = 0
        self.turn = 1
        self.level = level
        self.weights = [ self.level.prob[t] for t in CellType.NORMAL_SET ]
        self.candidates = candidates or rnd.choices(CellType.NORMAL_SET, weights=self.weights, k=1000)
        self.candidate_idx = 0
        self.cells = self._full_random()
        while self.explode_all():
            self.apply_fall(self.make_fall())
            self.fill()
        self.score = 0
 
    def _init_by_retries(self):
        while True:
            self.cells = self._full_random()
            any, _ = self.maybe_explode_all()
            if not any: break
    
    def get_candidates(self, n):
        r = []
        for _ in range(n):
            r.append(self.candidates[self.candidate_idx])
            self.candidate_idx = (self.candidate_idx + 1) % len(self.candidates)
        return r

    def _full_random(self):
        return [
            self.get_candidates(Field.SIZE)
            for _ in range(Field.SIZE) ]

    def fill(self):
        cnt = 0
        for y in range(Field.SIZE):
            for x in range(Field.SIZE):
                if self.cells[y][x] == CellType.EMPTY:
                    cnt += 1
        new_cells = self.get_candidates(cnt)
        cnt = 0
        for y in range(Field.SIZE):
            for x in range(Field.SIZE):
                if self.cells[y][x] == CellType.EMPTY:
                    self.cells[y][x] = new_cells[cnt]
                    cnt += 1
    
    @staticmethod
    def is_inside(pos):
        return 0 <= pos.x < Field.SIZE and 0 <= pos.y < Field.SIZE

    def can_swap(self, a, b):
        p = a - b
        if abs(p.x) + abs(p.y) != 1: return False
        self.swap(a, b)
        result = self.is_exploding(int(a.x), int(a.y)) or self.is_exploding(int(b.x), int(b.y))
        self.swap(a, b)
        return result
        #f = copy.deepcopy(self)
        #f.swap(a, b)
        #return f.is_exploding(int(a.x), int(a.y)) or f.is_exploding(int(b.x), int(b.y))
    
    def swap(self, a, b):
        a, b = map(v2int, [a, b])
        self.cells[a[1]][a[0]], self.cells[b[1]][b[0]] = self.cells[b[1]][b[0]], self.cells[a[1]][a[0]]

    def is_exploding(self, x, y):
        color = self.cells[y][x]
        def count(dx, dy):
            xx = x; yy = y; cnt = 0
            while self.is_inside(Vector2(xx, yy)) and self.cells[yy][xx] == color:
                xx += dx; yy += dy
                cnt += 1
            return cnt
        return (
            count(1, 0) + count(-1, 0) - 1 >= self.MIN_EXPLODE or
            count(0, 1) + count(0, -1) - 1 >= self.MIN_EXPLODE)

    def make_fall(self):
        result = []
        for x in range(Field.SIZE):
            i = Field.SIZE - 1
            for y in range(Field.SIZE - 1, -1, -1):
                if self.cells[y][x] != CellType.EMPTY:
                    if y < i:
                        result.append(((x, y),(x, i)))
                    i -= 1
        return result

    def apply_fall(self, fall):
        for src, dst in fall:
            self.cells[dst[1]][dst[0]] = self.cells[src[1]][dst[0]]
            self.cells[src[1]][dst[0]] = CellType.EMPTY
    
    def maybe_explode_all(self):
        explodes = [ [False] * Field.SIZE for _ in range(Field.SIZE) ]
        cnt = 1; score = 0
        for y in range(Field.SIZE):
            for x in range(1, Field.SIZE + 1):
                if (
                    x < Field.SIZE and self.cells[y][x] != CellType.EMPTY and
                    self.cells[y][x] == self.cells[y][x - 1]
                ):
                    cnt += 1
                else:
                    if cnt >= self.MIN_EXPLODE:
                        for i in range(x - cnt, x):
                            explodes[y][i] = True
                        score += cnt * Field.COST[self.cells[y][x - 1]]
                    cnt = 1
        cnt = 1
        for x in range(Field.SIZE):
            for y in range(1, Field.SIZE + 1):
                if (
                    y < Field.SIZE and self.cells[y][x] != CellType.EMPTY and
                    self.cells[y][x] == self.cells[y - 1][x]
                ):
                    cnt += 1
                else:
                    if cnt >= self.MIN_EXPLODE:
                        for i in range(y - cnt, y):
                            explodes[i][x] = True
                        score += cnt * Field.COST[self.cells[y - 1][x]]
                    cnt = 1
        return score, explodes

    def explode_all(self):
        score, explodes = self.maybe_explode_all()
        if score:
            for y in range(Field.SIZE):
                for x in range(Field.SIZE):
                    if explodes[y][x]:
                        self.cells[y][x] = CellType.EMPTY
        self.score += score
        return score

    def apply_move(self, a, b):
        self.turn += 1
        self.swap(a, b)

    def cost_at(self, p):
        return Field.COST[self.cells[int(p.y)][int(p.x)]]

class AI:
    def __init__(self, field):
        self.field = field

    def make_move(self):
        for y in range(Field.SIZE - 1): 
            for x in range(Field.SIZE - 1):
                p = Vector2(x, y)
                if self.field.can_swap(p, Vector2(x + 1, y)):
                    return (p, Vector2(x + 1, y))
                if self.field.can_swap(p, Vector2(x, y + 1)):
                    return (p, Vector2(x, y + 1))
        return None

    def make_all_moves(self):
        moves = []
        for y in range(Field.SIZE - 1): 
            for x in range(Field.SIZE - 1):
                p = Vector2(x, y)
                if self.field.can_swap(p, Vector2(x + 1, y)):
                    moves.append((p, Vector2(x + 1, y)))
                if self.field.can_swap(p, Vector2(x, y + 1)):
                    moves.append((p, Vector2(x, y + 1)))
        return moves

    def make_random_move(self):
        moves = self.make_all_moves()
        return rnd.choice(moves) if moves else None

    def make_low_move(self):
        moves = self.make_all_moves()
        return moves[-1] if moves else None

    def make_good_move(self):
        moves = self.make_all_moves()
        if not moves:
            return None
        best = moves[0]
        for m in moves[1:]:
            if  self.field.cost_at(m[0]) >= self.field.cost_at(best[0]):
                best = m
        return best

    def make_optimal_move(self):
        moves = self.make_all_moves()
        if not moves:
            return None
        best_score = 0
        best = None
        for m in moves[1:]:
            f = copy.deepcopy(self.field)
            f.apply_move(*m)
            f.explode_all()
            if f.score >= best_score:
                best_score = f.score
                best = m
        return best
