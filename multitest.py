from multiprocessing import Pool, cpu_count
from datetime import datetime
from time import sleep


def f(a):
    sleep(1)
    return a*a


if __name__ == "__main__":
    # p = Pool(cpu_count())
    # start = datetime.now()
    # print(p.map(f, range(16)))
    # end = datetime.now()
    # print(f"Done in {(end-start).total_seconds()}")

    def filter_positions(last_part_positions: dict, new_part_positions: dict) -> dict:
        r = dict()
        for docId, locs in new_part_positions.items():
            last_locations = last_part_positions.get(docId, None)
            if last_locations is not None:
                for l in locs:
                    if l - 1 in last_locations:
                        s = r[docId] = r.get(docId, set())
                        s.add(l)
        return r

    d1 = {1: {1, 20, 30}, 3: {2, 15, 10}}
    d2 = {1: {2, 20, 31}, 5: {10, 16, 20}, 3: {12}}

    print(filter_positions(d1, d2))

    pass
