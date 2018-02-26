import os; os.system("python optimized_build.py build_ext --inplace")
from optimized.spimi.dictionary import Dictionary
from search import BooleanSearch
from datetime import datetime
import sys


if __name__ == "__main__":

    start_time = datetime.now()
    dictionary = Dictionary('C:/Users/Sasha/PycharmProjects/InfoSearch/documents/txtAll')
    index_time = datetime.now() - start_time
    print(f"    Indexed in {index_time.total_seconds()} secs")
    print(f"Unique words count: {len(dictionary)}", end='\n\n')
    print(f"Dictionary in-memory size: ~{sys.getsizeof(dictionary)//1024}kB")
    print(f"Dictionary --total-- size: ~{dictionary.total_size()//1024}kB\n")

    bs = BooleanSearch(dictionary)
    while True:
        query = input(f"Enter your query |{bs.__class__.__name__}| (empty to quit): ")
        if not query:
            break

        documents = bs.execute(query)
        print(f"Found {len(documents)} results")
        for i, p in enumerate(documents):
            print(f"Result {(i+1)} (in {dictionary.get_document_filepath(p)}): \n{dictionary.get_document(p)}")
            if input() != "":
                break
