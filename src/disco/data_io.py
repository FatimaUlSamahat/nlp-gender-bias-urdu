import json
from pathlib import Path
import pandas as pd
from src.disco.names import names_dict
NAMES_DIR = Path("data/names")
def load_names(tgt_lang,names_dir=NAMES_DIR):
    """Return a DataFrame with columns male/female (row i = one male + one female name).

    If data/names/<lang>_names.json exists ({"male": [...], "female": [...]}) it is used
    (this is how Urdu names are supplied). Otherwise fall back to the authors' names_dict.
    """
    nms_f = Path(names_dir)/f"{tgt_lang}_names.json"
    if nms_f.exists():
        with open(nms_f,"r",encoding="utf-8") as f:
            d=json.load(f)
        m_nms,fe_nms=d["male"],d["female"]
    elif tgt_lang in names_dict:
        m_nms=names_dict[tgt_lang]["male"]
        fe_nms=names_dict[tgt_lang]["female"]
    else:
        raise FileNotFoundError(f"Names for language '{tgt_lang}' not found: add {nms_f} or an entry in src/disco/names.py")
    if len(m_nms)!=len(fe_nms):
        raise ValueError(f"Male/female name lists for language '{tgt_lang}' have different lengths: {len(m_nms)} vs {len(fe_nms)}")
    # The authors' lists contain a few names with stray leading/trailing spaces (e.g. 'अनिल ');
    # strip them so they cannot change tokenization.
    m_nms=[n.strip() for n in m_nms]
    fe_nms=[n.strip() for n in fe_nms]
    return pd.DataFrame({"male":m_nms,"female":fe_nms})
def load_temps(templates_file,debug=False):
    """Load {"male": [...], "female": [...]} templates (authors' format)."""
    with open(templates_file,"r",encoding="utf8") as f:
        temps=json.load(f)
    if debug:
        temps={k:v[:2]for k,v in temps.items()}
    return temps
def validate(temps,nms):
    """Raise AssertionError with a clear message if the data would break the scorer."""
    assert set(temps)>={"male","female"},"templates need keys 'male' and female'"
    assert len(temps["male"])==len(temps["female"])>0,"templates['male'] and templates['female'] must have the same length"
    assert len(nms)>0 and not nms.isna().any().any(),"empty or missing names"
    for gender in ("male","female"):
        for t in temps[gender]:
            assert t.count("{PERSON}")==1,f"need exactly one {{PERSON}}:{t}"
            assert t.count("{BLANK}")==1,f"need exactly one {{BLANK}}:{t}"
    for col in ("male","female"):
        assert nms[col].map(lambda x: isinstance(x,str) and x.strip()==x and x!="").all(),f"blank or padded names in {col}"