from game import *
import numpy as np
from time import process_time
import json

def analyze_ai1():
    for level in LEVELS:
        scores = []
        for epoch in range(30):
            field = Field(level, rnd)
            ai = AI(field)
            for turn in range(10):
                m = ai.make_low_move()
                field.apply_move(*m)
                while field.explode_all():
                    field.apply_fall(field.make_fall())
                    field.fill()
            scores.append(field.score)
        print(f"Level: {level.name}")#" scores: {scores}")
        print(f"Average = {np.mean(scores)} Stddev = {np.std(scores)}")

def analyze_ai2():
    level_scores = []
    for level in LEVELS:
        epoch_scores = []
        for epoch in range(30):
            field = Field(level, rnd)
            ai = AI(field)
            seed = rnd.randint(1, 1000000)
            fns = [ ai.make_move, ai.make_low_move, ai.make_optimal_move ]
            fn_scores = []
            for fn in fns:
                rnd.seed(seed)
                f = ai.field = copy.deepcopy(field)
                s = []
                for turn in range(10):
                    m = fn()
                    f.apply_move(*m)
                    while f.explode_all():
                        f.apply_fall(f.make_fall())
                        f.fill()
                    s.append(f.score)
                fn_scores.append(s)
            epoch_scores.append(fn_scores)
        print(f"Level: {level.name} scores: {np.array(epoch_scores).shape}")
        level_scores.append(epoch_scores)
        json.dump(level_scores, open("scores.json", "w"))
        #print(f"Average = {np.mean(scores)} Stddev = {np.std(scores)}")


def zeroes(n): return [ [0]*n for _ in range(n) ]

def analyze_ai3():
    cnts = [ [ zeroes(Field.SIZE) for f in range(3) ] for _ in LEVELS ]
    for level_idx, level in enumerate(LEVELS):
        for epoch in range(30):
            field = Field(level, rnd)
            ai = AI(field)
            fns = [ ai.make_move, ai.make_low_move, ai.make_optimal_move ]
            seed = rnd.randint(1, 1000000)
            for fn_idx, fn in enumerate(fns):
                rnd.seed(seed)
                f = ai.field = copy.deepcopy(field)
                s = []
                for turn in range(10):
                    m = fn()
                    f.apply_move(*m)
                    a, b = map(v2int, m)
                    cnts[level_idx][fn_idx][a[1]][a[0]] += 1
                    cnts[level_idx][fn_idx][b[1]][b[0]] += 1
                    while f.explode_all():
                        f.apply_fall(f.make_fall())
                        f.fill()
        print(f"Level: {level.name}")
        json.dump(cnts, open("cnts.json", "w"))
        #print(f"Average = {np.mean(scores)} Stddev = {np.std(scores)}")

def generate_level(level_idx):
    level = LEVELS[level_idx]
    best_moves = 1e6
    best = []
    totals = []
    for epoch in range(100):
        field = Field(level, rnd)
        ai = AI(field)
        total_moves = 0
        for turn in range(10):
            moves = ai.make_all_moves()
            total_moves += len(moves)
            m = ai.make_low_move()
            field.apply_move(*m)
            while field.explode_all():
                field.apply_fall(field.make_fall())
                field.fill()
        totals.append(total_moves)
        if total_moves < best_moves:
            best_moves = total_moves
            best = field.candidates
    print(f"Level: {level.name}")
    json.dump({'candidates': best}, open("level.json", "w"))
    print(f"Average = {np.mean(totals)} Stddev = {np.std(totals)} Best = {best_moves}")

start_t = process_time()
analyze_ai2()
print(f"Time: {process_time() - start_t}")