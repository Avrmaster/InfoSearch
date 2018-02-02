import os; os.system("python optimized_build.py build_ext --inplace")
from optimized.dictionary import Dictionary
from search import BooleanSearch, PhraseSearch, PositionalSearch
from datetime import datetime
import sys


if __name__ == "__main__":
    dictionary = Dictionary()
    start_time = datetime.now()
    dictionary.add_dir('documents/txtAll')
    end_time = datetime.now()
    print(f"    Indexed in {(end_time-start_time).total_seconds()} secs")
    # print(dictionary, end='\n\n')
    print(f"Unique words count: {len(dictionary)}", end='\n\n')
    print(f"Dictionary system size: ~{sys.getsizeof(dictionary)//1024}kB\n")

    # bs = BooleanSearch(dictionary)
    # bs = PhraseSearch(dictionary)
    bs = PositionalSearch(dictionary)
    while True:
        query = input("Enter your query (empty to quit): ")
        if not query:
            break
        paragraphs = bs.execute(query)
        print(f"Found {len(paragraphs)} results")
        for i, p in enumerate(paragraphs):
            print(f"Result {(i+1)} (in {dictionary.get_paragraph_info(p)[0]}): \n{dictionary.get_paragraph(p)}")
            if input() != "":
                break
