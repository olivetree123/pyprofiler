import re


# line = "1731479646475  return [inner] on line:0 of /usr/local/lib/python3.10/site-packages/django/utils/functional.py totally 0.022649765014648438 ms coast"
# r = re.match(r"(\d+)\s+(\w+)\s+(\[\w+\])\s+(\w+)\s+(\w+:\d+)\s+\w+\s+(\S+)\s+totally\s+([\d\.]+)\s+ms\s+coast", line)
# if not r:
#     print("no match")
# print(r.groups())

# with open("pyprofiler.txt", "r", encoding="utf8") as f:
#     for line in f.readlines():
#         r = re.match(r"(\d+)\s+(\w+)\s+(\[\w+\])\s+(\w+)\s+(\w+:\d+)\s+\w+\s+(\S+)\s+totally\s+([\d\.]+)\s+ms\s+coast", line)
#         if not r:
#             continue
#         result = r.groups()
#         if float(result[-1]) > 500:
#             print(result)
            

def analyse(filepath: str = "pyprofiler.txt"):
    with open(filepath, "r", encoding="utf8") as f:
        for line in f.readlines():
            r = re.match(r"(\d+)\s+(\w+)\s+(\[\w+\])\s+(\w+)\s+(\w+:\d+)\s+\w+\s+(\S+)\s+totally\s+([\d\.]+)\s+ms\s+coast", line)
            if not r:
                continue
            result = r.groups()
            if float(result[-1]) > 500:
                print(result)