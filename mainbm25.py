import os; os.system("python optimized_build.py build_ext --inplace")
from optimized.bm25.dictionary import Dictionary
from datetime import datetime
from utils.files import get_total_files_size_in_directory


if __name__ == "__main__":
    # documents_path = 'C:/Users/Sasha/PycharmProjects/InfoSearch/documents/txt'
    documents_path = 'C:/Users/Sasha/PycharmProjects/InfoSearch/documents/txtAll'

    extension = "txt"

    print(f"Initializing indexing algorithm. Collection to index lays in directory {documents_path}."
          f" Total size to index: ")
    index_collection_size = get_total_files_size_in_directory(documents_path, extension)
    print(f"{index_collection_size//1024/1024} mb.")

    start_time = datetime.now()
    dictionary = Dictionary(documents_path, extension)
    index_time = datetime.now() - start_time
    print(f"    Indexed in {index_time.total_seconds()} secs"
          f" ({index_collection_size/index_time.total_seconds()/1024/1024} mb/sec)")

    while True:
        query = input(f"Enter your query ('\quit' to quit): ").lower()
        if query == "\quit":
            break

        result_documents_paths = dictionary.best(10, query)
        print(f"Found {len(result_documents_paths)} results:")
        print('\n'.join(result_documents_paths))
