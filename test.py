# import os; os.system("python optimized_build.py build_ext --inplace")
from optimized.spimi.dictionary import Dictionary
from datetime import datetime
import sys
import re


if __name__ == "__main__":

    # start_time = datetime.now()
    # dictionary = Dictionary('C:/Users/Sasha/PycharmProjects/InfoSearch/documents/txt')
    # # dictionary = Dictionary('D:/ToIndex/gutenberg')
    # index_time = datetime.now() - start_time
    # print(f"    Indexed in {index_time.total_seconds()} secs")
    # print(f"Unique words count: {len(dictionary)}", end='\n\n')
    # print(f"Dictionary in-memory size: ~{sys.getsizeof(dictionary)//1024}kB")
    # print(f"Dictionary --total-- size: ~{dictionary.total_size()//1024}kB\n")

    s = "''-dk'dj-ash,'-,"
    strip_ex = re.compile(r"[^\w'\-]|^['\-]+|['\-]+$", flags=re.IGNORECASE)

    print(strip_ex.sub("", s))
