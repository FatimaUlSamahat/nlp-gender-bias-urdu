"""Check template and name files WITHOUT loading any model (fast, no GPU).

Usage:  python -m src.disco.check_data --lang ur
Prints counts and every male/female template pair so you can eyeball them.
"""
import argparse
from pathlib import Path
from src.disco.data_io import load_names, load_temps, validate
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang",required=True)
    ap.add_argument("--templates_dir",default="data/templates")
    ap.add_argument("--templates_file",default=None)
    args=ap.parse_args()
    path = Path(args.templates_file) if args.templates_file else Path(args.templates_dir)/f"disco_templates_{args.lang}.json"
    temps,nms = load_temps(path),load_names(args.lang)
    validate(temps,nms)
    print(f"OK: {path} -> {len(temps['male'])} template pairs, {len(nms)} male + {len(nms)} female names")
    same = sum(m==f for m,f in zip(temps["male"],temps["female"]))
    print(f"{same} of {len(temps['male'])}pairs have identical male/female templates (e.g. {temps['male'][0]} vs {temps['female'][0]})")
    for i,(m,f) in enumerate(zip(temps["male"],temps["female"]),1):
        print(f"{i:2d} M:{m}")
        if f!=m:
            print(f"   F:{f}")
    dup_m,dup_f=len(nms)-nms["male"].nunique(),len(nms)-nms["female"].nunique()
    both=set(nms["male"])&set(nms["female"])
    print(f"{dup_m} duplicate male names, {dup_f} duplicate female names, names in both lists: {len(both)}")
if __name__=="__main__":
    main()

