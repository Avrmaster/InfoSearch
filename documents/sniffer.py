import requests
import urllib3
import certifi
import re
import os


href_re = re.compile("""href=["'](.+?)["']""", flags=re.IGNORECASE)
start_addr = 'http://textfiles.com/etext/'
queue = [start_addr]
output_dir = 'txt'
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where())
downloaded = []
visited = set()


while len(queue) > 0:
    cur_address = queue.pop(0)
    if cur_address not in visited:
        visited.add(cur_address)
    else:
        print(f"\r{cur_address} was already visited", end='')
        continue
    print(f"\rSniffing.. {cur_address}", end='')
    try:
        page_text = requests.get(cur_address).text
    except:
        continue
    for ref in href_re.finditer(page_text):
        new_addr = ref[1]
        if 'http' not in new_addr:
            new_addr = f'{cur_address}/{new_addr}'
        elif start_addr not in new_addr:
            print(f"\rSkipping foreign page {new_addr}", end='')
            continue
        if new_addr.endswith('.txt') or new_addr.endswith('text'):
            filename: str = (new_addr[new_addr.rindex('/')+1:]).replace('%20', ' ')
            if not filename.endswith('.txt'):
                filename += ".txt"

            if filename not in os.listdir(output_dir):
                try:
                    print(f"\rDownloading {filename}", end='')
                    downloaded_file = http.request('GET', new_addr).data
                    with open(f"{output_dir}/{filename}", 'wb+') as out:
                        out.write(downloaded_file)
                    downloaded.append(filename)
                except Exception as e:
                    print(f"Skipping {filename} because of {e}\n")
            else:
                print(f"\rSkipping {filename} because it already downloaded", end='')
        else:
            queue.append(new_addr)
print("Done. Downloaded: \n{}\n Total: {}".format('\n'.join(downloaded), len(downloaded)))
