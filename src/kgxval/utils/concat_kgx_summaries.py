import os
import datetime
import pandas as pd

def getLatestRunDir():
    fmt = "%b-%d-%y"
    l = list(zip([datetime.datetime.strptime(x,fmt) for x in os.listdir("data/output")],os.listdir("data/output")))
    latest_dir = max(l)[1]
    print(f"Latest run was made on - {latest_dir}")
    return os.path.join("data","output",latest_dir)

print(os.listdir(getLatestRunDir()))

def getNorm(xlsx_file_path):
    ef = pd.ExcelFile(xlsx_file_path)
    assert len([x for x in ef.sheet_names if "normalized_summary" in x])==1, f"BAD, {xlsx_file_path}"
    norm_sheet = [x for x in ef.sheet_names if "normalized_summary" in x][0]
    norm_df = pd.read_excel(ef,norm_sheet)
    return norm_df

latest_dir = getLatestRunDir()
mega_df = pd.DataFrame()
for x in os.listdir(latest_dir):
    if(not x.endswith('.xlsx')):continue
    if(("merge" in x) or ("combine" in x)):continue
    norm_df = getNorm(os.path.join(latest_dir,x))
    print(x,norm_df)
    mega_df = pd.concat([mega_df,norm_df])
from pathlib import Path
latest_date = Path(latest_dir).stem
writer = pd.ExcelWriter(os.path.join("data/output",latest_date,f"_concatted_summaries_{latest_date}.xlsx"))
mega_df.to_excel(writer,sheet_name=f"{latest_date}_combined",index=False)
writer.close()