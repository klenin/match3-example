from game import *
import numpy as np
from time import process_time

def analyze_ai1():
    for level in LEVELS:
        scores = []
        for epoch in range(30):
            field = Field(level)
            ai = AI(field)
            for turn in range(10):
                m = ai.make_optimal_move()
                field.apply_move(*m)
                while field.explode_all():
                    field.apply_fall(field.make_fall())
                    field.fill()
            scores.append(field.score)
        print(f"Level: {level.name}")#" scores: {scores}")
        print(f"Average = {np.mean(scores)} Stddev = {np.std(scores)}")

def analyze_ai2():
    for level in LEVELS:
        scores = []
        for epoch in range(10):
            field = Field(level)
            ai = AI(field)
            seed = rnd.randint(1, 1000000)
            fns = [ ai.make_optimal_move, ai.make_low_move ]
            s = []
            for fn in fns:
                rnd.seed(seed)
                f = ai.field = copy.deepcopy(field)
                for turn in range(10):
                    m = fn()
                    f.apply_move(*m)
                    while f.explode_all():
                        f.apply_fall(f.make_fall())
                        f.fill()
                s.append(f.score)
            scores.append(s)
        print(f"Level: {level.name} scores: {scores}")
        #print(f"Average = {np.mean(scores)} Stddev = {np.std(scores)}")

start_t = process_time()
analyze_ai2()
print(f"Time: {process_time() - start_t}")