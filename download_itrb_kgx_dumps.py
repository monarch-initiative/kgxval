import subprocess
import json
from datetime import datetime
import os

cmd1 = ["wget", "https://kgx-storage.ci.transltr.io/releases/latest-release-summary.json", "-O", "ignore/latest-release-summary.json"]

#subprocess.run(cmd1, check=True)
#cd ignore
#wget 

datestr = datetime.now().strftime("%b-%d-%y")  # ex. Feb-16-2026
with open("ignore/latest-release-summary.json") as f:
    latest = json.load(f)

for infores in latest:
    url = f"https://kgx-storage.rtx.ai/releases/{infores}/latest/{infores}.tar.zst"
    outdir = f"/scratch/tmp/dkorn/TRANSLATOR-KGX/{datestr}/{infores}"
    print(outdir)
    os.makedirs(outdir, exist_ok=True)
    dl_cmd = ["wget", url, "-O", os.path.join(outdir,f"{infores}.tar.zst")]
    print(dl_cmd)
    if(os.path.exists(f"/scratch/tmp/dkorn/TRANSLATOR-KGX/{datestr}/{infores}/{infores}.tar.zst")):continue
    subprocess.run(dl_cmd, check=True)

for infores in latest:
    infores_dir = f"/scratch/tmp/dkorn/TRANSLATOR-KGX/{datestr}/{infores}"
    zst_file = f"{infores_dir}/{infores}.tar.zst"

    ext_cmd = ["tar", "--use-compress-program=zstd", "-xf", zst_file, "-C", infores_dir]
    print(ext_cmd)
    if(not os.path.exists(f"/scratch/tmp/dkorn/TRANSLATOR-KGX/{datestr}/{infores}/{infores}.tar.zst")):continue
    if(os.path.exists(f"/scratch/tmp/dkorn/TRANSLATOR-KGX/{datestr}/{infores}/nodes.jsonl")):
        print("Already extracted.")
        continue
    subprocess.run(ext_cmd, check=True)