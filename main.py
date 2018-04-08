import os; os.system("python optimized_build.py build_ext --inplace")
from optimized.spimi.dictionary import Dictionary
from search import BooleanSearch
from datetime import datetime
from utils.files import get_total_files_size_in_directory
import sys


if __name__ == "__main__":
    # documents_path = 'C:/Users/Sasha/PycharmProjects/InfoSearch/documents/txt'
    # documents_path = 'C:/Users/Sasha/PycharmProjects/InfoSearch/documents/txtAll'
    # documents_path = 'C:/Users/Sasha/PycharmProjects/InfoSearch/documents/gutenPartSmall'
    # documents_path = 'C:/Users/Sasha/PycharmProjects/InfoSearch/documents/fb2'
    documents_path = 'C:/Users/Sasha/PycharmProjects/InfoSearch/documents/fb2All'
    # documents_path = 'D:/ToIndex/gutenberg'

    # extension = "txt"
    extension = "fb2"

    print(f"Initializing indexing algorithm. Collection to index lays in directory {documents_path}."
          f" Total size to index: ")
    index_collection_size = get_total_files_size_in_directory(documents_path, extension)
    print(f"{index_collection_size//1024/1024} mb.")

    start_time = datetime.now()
    dictionary = Dictionary(documents_path, extension)
    index_time = datetime.now() - start_time
    print(f"    Indexed in {index_time.total_seconds()} secs"
          f" ({index_collection_size/index_time.total_seconds()/1024/1024} mb/sec)")
    print(f"Unique words count: {len(dictionary)}", end='\n\n')
    print(f"    Dictionary in-memory size: ~{sys.getsizeof(dictionary)/1024/1024} mB")
    print(f"    Dictionary --total-- size: ~{dictionary.total_size()/1024/1024} mB\n")

    bs = BooleanSearch(dictionary)
    while True:
        query = input(f"Enter your query |{bs.__class__.__name__}| ('\quit' to quit): ")
        if query == "\quit":
            break

        documents_ids = bs.ranked_execute(query)
        print(f"Found {len(documents_ids)} results:")
        print('\n'.join(tuple(dictionary.get_document_filepath(doc_id) for doc_id in documents_ids)))
        for i, p in enumerate(documents_ids):
            if input() != "":
                break
            print(f"Result {(i+1)} (in {dictionary.get_document_filepath(p)}): \n{dictionary.get_document(p)}")

    dictionary.remove_temp_files()
