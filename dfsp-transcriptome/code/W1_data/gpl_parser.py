"""W1: 通用 GPL 注释解析器（兼容 SOFT 表格与 #ID= 块两种格式）"""
import gzip, re, pandas as pd

def load_gpl_annot(path):
    """返回 dict{probe_id: gene_symbol}"""
    opener = gzip.open if str(path).endswith(".gz") else open
    mapping = {}
    with opener(path, "rt", errors="replace") as f:
        text = f.read()
    # 格式1: !platform_table_begin 后的 tab 表
    if "!platform_table_begin" in text:
        head, _, body = text.partition("!platform_table_begin")
        lines = [l for l in body.splitlines() if l.strip()]
        header = [h.strip('"').strip() for h in lines[0].split("\t")]
        id_col = next((i for i, h in enumerate(header) if h.upper() in ("ID", "ID_REF", "PROBE_ID", "PROBEID")), None)
        gene_col = next((i for i, h in enumerate(header) if h.upper() in ("GENE_SYMBOL", "SYMBOL", "GENE", "GENE NAME", "GENE_SYMBOL", "GENEASSIGNMENT")), None)
        if id_col is None or gene_col is None:
            # 尝试宽松匹配
            if id_col is None:
                id_col = 0
            if gene_col is None:
                for i, h in enumerate(header):
                    if "SYMBOL" in h.upper() or "GENE" in h.upper():
                        gene_col = i; break
        if id_col is not None and gene_col is not None:
            for l in lines[1:]:
                parts = l.split("\t")
                if len(parts) <= max(id_col, gene_col):
                    continue
                pid = parts[id_col].strip().strip('"')
                g = parts[gene_col].strip().strip('"')
                if pid and g and g.upper() != "NA":
                    mapping.setdefault(pid, g)
            if mapping:
                return mapping
    # 格式2: 逐行 #ID = / #Gene =
    cur_id = None
    for line in text.splitlines():
        if line.startswith("#ID"):
            cur_id = line.split("=", 1)[1].strip()
        elif line.startswith("#Gene") and cur_id:
            g = line.split("=", 1)[1].strip()
            if g:
                mapping.setdefault(cur_id, g)
    return mapping

def load_family_platform(path, id_col="ID", symbol_col="Symbol"):
    """流式解析 family.soft.gz 的平台表（只读平台段，不读 GSM 数据），返回 {probe_id: gene_symbol}"""
    opener = gzip.open if str(path).endswith(".gz") else open
    mapping = {}
    in_table = False
    i_id = i_sym = None
    with opener(path, "rt", errors="replace") as f:
        for line in f:
            s = line.rstrip("\n")
            if s.startswith("!platform_table_begin"):
                in_table = True
                continue
            if s.startswith("!platform_table_end"):
                break
            if not in_table:
                continue
            parts = s.split("\t")
            if len(parts) < 2:
                continue
            if parts[0] == id_col:  # 表头行
                try:
                    i_id = parts.index(id_col)
                    i_sym = parts.index(symbol_col)
                except ValueError:
                    return {}
                continue
            if i_id is None or len(parts) <= max(i_id, i_sym or 0):
                continue
            pid = parts[i_id].strip()
            sym = parts[i_sym].strip()
            if pid and sym and sym.upper() not in ("NA", "NONE"):
                mapping.setdefault(pid, sym)
    return mapping

def normalize_symbols(mapping):
    """基因符号清洗：去掉 // 多注释只取第一个，去空格"""
    out = {}
    for k, v in mapping.items():
        v = re.split(r"[///]", v)[0].strip()
        v = v.split(" ")[0].strip()
        if v and v.upper() != "NA" and not v.startswith("---"):
            out[k] = v
    return out

if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        m = load_gpl_annot(p)
        m = normalize_symbols(m)
        print(f"{p}: {len(m)} 个探针映射")
        for k in list(m)[:5]:
            print(f"   {k} -> {m[k]}")
