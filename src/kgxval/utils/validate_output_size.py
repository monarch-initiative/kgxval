from datetime import datetime
import requests
from bs4 import BeautifulSoup
import os

def getInforesListFromITRB():
    data_url = "https://kgx-storage.ci.transltr.io/data/"
    soup = BeautifulSoup(requests.get(data_url).text,'html.parser')

    inforeses = []

    for dirs in soup.find_all("a",class_="tree-item"):
        #print(dirs)
        y = dirs.find(class_="tree-name")
        name = y.contents[2].strip()
        inforeses.append(name)
    return inforeses

def getInforesSummaryList(output_dir):
    summ_files = os.listdir(output_dir)
    summ_files = [x for x in summ_files if (("merge" not in x) and ("combine" not in x) and x.endswith("xlsx"))]
    inforeses = ["_".join(x.split("_")[0:-2]) for x in summ_files]
    return inforeses

def main(output_dir):
    infores_from_itrb = getInforesListFromITRB()
    infores_from_summ = getInforesSummaryList(output_dir)
    print(f"Infores from ITRB's site is {len(infores_from_itrb)}")
    print(f"Infores summarized in f{output_dir} is {len(infores_from_summ)}")
    diff = set(infores_from_itrb).difference(infores_from_summ)
    print(f"Missing infores are {sorted(list(diff))}")
    assert(len(infores_from_itrb)==len(set(infores_from_itrb).intersection(infores_from_summ)))

if(__name__=="__main__"):
    import sys
    output_dir = sys.argv[1]
    main(output_dir)