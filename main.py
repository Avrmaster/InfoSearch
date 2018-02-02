import os; os.system("python optimized_build.py build_ext --inplace")
from optimized.dictionary import Dictionary
from cachetools import cached, LFUCache
from booleanSearch import BooleanSearch
from datetime import datetime
import sys


if __name__ == "__main__":
    dictionary = Dictionary()
    start_time = datetime.now()
    paragraphs_map = dictionary.add_dir('documents/txtAll')
    end_time = datetime.now()
    print(f"    Indexed in {(end_time-start_time).total_seconds()} secs")
    # print(dictionary, end='\n\n')
    print(f"Total paragraph count: {len(paragraphs_map)}")
    print(f"Unique words count: {len(dictionary)}", end='\n\n')
    print(f"Dictionary system size: ~{sys.getsizeof(dictionary)//1024}kB\n")

    @cached(cache=LFUCache(maxsize=300))
    def get_paragraph(p_id: int):
        fpath, lnum = paragraphs_map[p_id]
        with open(fpath) as f:
            for j, l in enumerate(f):
                print(f"\ropening{'.'*(j%3)+' '*(3-j%3)}{(j+1)*100//(lnum+1)}%", end='')
                if j == lnum:
                    print(end='\r')
                    return l


    bs = BooleanSearch(dictionary)
    while True:
        query = input("Enter your query (empty to quit): ")
        if not query:
            break
        paragraphs = bs.execute(query)
        print(f"Found {len(paragraphs)} results")
        for i, p in enumerate(paragraphs):
            print(f"Result {(i+1)} (in {paragraphs_map[p][0]}): \n{get_paragraph(p)}")
            if input() != "":
                break
