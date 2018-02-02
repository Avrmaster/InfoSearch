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

    print(f"{'hello'[0:1]}")

    pass
