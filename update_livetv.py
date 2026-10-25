import os
import re
import sys
import unicodedata
import requests

SOURCES = [
    "https://raw.githubusercontent.com/khanh71/All-In-One-IPTV/main/http-iptv.m3u",
    "https://dl.dropboxusercontent.com/s/o5vygit34v9ryly71gam4/coban66.m3u?rlkey=auyoon54hfubajt16nc7u7dbn&st=70gyvtcu&dl=0"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D')

def normalize_key(text: str) -> str:
    cleaned = strip_accents(text)
    return re.sub(r'[\s\-_.()]+', '', cleaned).upper()

# 1. Fetch remote sources
remote_channels = {}
for src in SOURCES:
    print(f"Fetching source: {src} ...")
    try:
        r = requests.get(src, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            lines = r.text.splitlines()
            cur_extinf = None
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    cur_extinf = line
                elif line and not line.startswith("#") and cur_extinf:
                    raw_name = cur_extinf.split(",")[-1].strip()
                    key = normalize_key(raw_name)
                    if key not in remote_channels:
                        remote_channels[key] = {
                            "name": raw_name,
                            "url": line,
                            "extinf": cur_extinf
                        }
                    cur_extinf = None
    except Exception as e:
        print(f"Error fetching {src}: {e}")

print(f"Indexed {len(remote_channels)} unique channels from upstream sources.")

# 2. Channel matching aliases
ALIASES = {
    "VTV1HD1080P": ["VTV1", "VTV1HD"],
    "VTV2HD1080P": ["VTV2", "VTV2HD"],
    "VTV3HD1080P": ["VTV3", "VTV3HD"],
    "VTV4HD1080P": ["VTV4", "VTV4HD"],
    "VTV61080P": ["VTV6", "VTV6HD"],
    "VTV7HD1080P": ["VTV7", "VTV7HD"],
    "HTV1720P": ["HTV1", "HTV1HD"],
    "HTV2720P": ["HTV2", "HTV2HD"],
    "HTV3720P": ["HTV3", "HTV3HD"],
    "HTV41080P": ["HTV4", "HTV4HD"],
    "HTV7720P": ["HTV7", "HTV7HD"],
    "HTV9720P": ["HTV9", "HTV9HD"],
    "HTVSPORTS": ["HTVCTHETHAO", "HTVTHETHAO", "HTVCTHETHAOHD", "HTVSPORTS"],
    "VOVGIAOTHONGTPHCM": ["VOVGIAOTHONGTPHCM", "VOVGIAOTHONG"]
}

# 3. Read existing LiveTV.m3u
m3u_file = "LiveTV.m3u"
if not os.path.exists(m3u_file):
    print(f"Error: {m3u_file} not found!")
    sys.exit(1)

with open(m3u_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

output_lines = []
cur_extinf = None

for line in lines:
    line_clean = line.strip()
    if line_clean.startswith("#EXTINF"):
        cur_extinf = line_clean
        output_lines.append(line_clean)
    elif line_clean.startswith("#"):
        output_lines.append(line_clean)
    elif line_clean and cur_extinf:
        orig_name = cur_extinf.split(",")[-1].strip()
        norm_name = normalize_key(orig_name)
        is_vn = any(prefix in norm_name for prefix in ["VTV", "HTV", "VOV"])
        
        new_url = line_clean
        if is_vn:
            keys_to_try = ALIASES.get(norm_name, [norm_name])
            for k in keys_to_try:
                matched = False
                for rem_k, rem_val in remote_channels.items():
                    if k == rem_k or k in rem_k or rem_k in k:
                        new_url = rem_val["url"]
                        matched = True
                        break
                if matched:
                    break
                    
            if orig_name == "HTV4 (1080p)" and "freem3u.xyz" in new_url:
                new_url = "https://dethich.pw/htv4/index.m3u8"
                
        output_lines.append(new_url)
        cur_extinf = None

with open(m3u_file, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines) + "\n")

print(f"Successfully updated {m3u_file}!")
