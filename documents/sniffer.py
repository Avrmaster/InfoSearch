import requests
import urllib3
import certifi
import re
import os


href_re = re.compile("""href=["'](.+?)["']""", flags=re.IGNORECASE)
start_addr = 'http://textfiles.com/etext'
queue = [start_addr]
output_dir = 'txt'
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where())
downloaded = []
visited = set()


def _save(content, filename: str, plain_text: bool = False):
    print(f"\rSaving {'plain' if plain_text else ''} {filename}", end='')
    try:
        if plain_text:
            with open(f"{output_dir}/{filename}", 'w+', encoding='utf-8') as out:
                out.write(content)
        else:
            with open(f"{output_dir}/{filename}", 'wb+') as out:
                out.write(content)
    except Exception as e:
        print(f"Skipping saving {filename} because of {e}\n")
    downloaded.append(filename)


def _link_to_filename(link: str):
    name = (link[link.rindex('/')+1:]).replace('%20', ' ')
    if not name.endswith('.txt'):
        name += '.txt'
    return name


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
    except Exception as e:
        print("Couldn't download")
        continue

    if '<html' not in (page_text[:15]).lower():
        _save(page_text, _link_to_filename(cur_address), plain_text=True)
    else:
        for ref in href_re.finditer(page_text):
            new_addr = ref[1]
            if 'http' not in new_addr:
                new_addr = f'{cur_address}/{new_addr}'
            elif start_addr not in new_addr:
                print(f"\rSkipping foreign page {new_addr}", end='')
                continue
            if new_addr.endswith('.txt') or new_addr.endswith('text'):
                filename: str = _link_to_filename(new_addr)
                if filename not in os.listdir(output_dir):
                    downloaded_bytes = http.request('GET', new_addr).data
                    _save(downloaded_bytes, filename)
                else:
                    print(f"\rSkipping downloading {filename} because it already exist", end='')
            else:
                queue.append(new_addr)
print("\nDone. Downloaded: \n{}\nTotal: {}".format('\n'.join(downloaded), len(downloaded)))
