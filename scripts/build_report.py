"""Fill the supplemental referee report template.
Usage: python3 build_report.py SPEC.json TEMPLATE.docx DIAGRAM_DIR OUT_DIR
Writes OUT_DIR/<filename>.docx and .pdf for each report in SPEC["reports"], plus OUT_DIR/<game>_app.txt (combined plain text).
"""
import sys, os, re, json, shutil, subprocess, zipfile, tempfile
from xml.sax.saxutils import escape
spec = json.load(open(sys.argv[1])); TPL = sys.argv[2]; DD = sys.argv[3]; OUT = sys.argv[4]
os.makedirs(OUT, exist_ok=True)
F = '<w:rFonts w:asciiTheme="minorHAnsi" w:hAnsiTheme="minorHAnsi"/>'
PPR = '<w:pPr><w:pStyle w:val="NormalWeb"/><w:rPr>' + F + '</w:rPr></w:pPr>'
def t(s): return '<w:t xml:space="preserve">' + escape(s) + '</w:t>'
def lab(s): return '<w:r><w:rPr><w:rStyle w:val="Strong"/>' + F + '</w:rPr>' + t(s) + '</w:r>'
def txt(s): return '<w:r><w:rPr>' + F + '</w:rPr>' + t(s) + '</w:r>'
BR = '<w:r><w:rPr>' + F + '</w:rPr><w:br/></w:r>'
def block(lines):
    out = []
    for i, (l, v) in enumerate(lines):
        if i: out.append(BR)
        out += [lab(l), txt(' ' + v)]
    return '<w:p>' + PPR + ''.join(out) + '</w:p>'
def para(label, body): return '<w:p>' + PPR + (lab(label) + txt(' ' + body) if label else txt(body)) + '</w:p>'
def image(rid, pid, name, w_in=3.4, ratio=700/760):
    cx = int(w_in * 914400); cy = int(cx * ratio)
    return ('<w:p><w:pPr><w:pStyle w:val="NormalWeb"/><w:jc w:val="center"/><w:rPr>' + F + '</w:rPr></w:pPr><w:r><w:rPr>' + F + '</w:rPr><w:drawing>'
      f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
      f'<wp:docPr id="{pid}" name="Diagram {pid}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
      '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
      f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{pid}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
      f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
      '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')

h = spec["header"]
HDR = [("Date / Time:", h["date_time"]), ("Location:", h["location"]), ("Event:", h["event"]), ("Referee:", h["referee"])]
if h.get("assistant_referees"): HDR.append(("Assistant Referees:", h["assistant_referees"]))
GAME = [("Game Number:", h["game_number"]), ("Home Team:", h["home"]), ("Away Team:", h["away"])]

def soffice_pdf(docx, outdir):
    for cmd in (["soffice"], ["libreoffice"]):
        try:
            subprocess.run(cmd + ["--headless", "--convert-to", "pdf", "--outdir", outdir, docx], check=True, capture_output=True, timeout=180); return True
        except Exception: pass
    return False

plain = []
for rep in spec["reports"]:
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(TPL) as z: z.extractall(work)
    dp = os.path.join(work, "word/document.xml"); doc = open(dp, encoding="utf-8").read()
    head, rest = doc.split("<w:body>", 1); old_body = rest[:rest.index("<w:sectPr")]; sect = rest[rest.index("<w:sectPr"):]
    rp = os.path.join(work, "word/_rels/document.xml.rels"); rels = open(rp, encoding="utf-8").read()
    for rid in set(re.findall(r'r:embed="([^"]+)"', old_body)):           # drop images used only by the old body
        m = re.search(r'<Relationship [^>]*Id="%s"[^>]*Target="([^"]+)"[^>]*/>' % rid, rels) or re.search(r'<Relationship [^>]*Target="([^"]+)"[^>]*Id="%s"[^>]*/>' % rid, rels)
        if m:
            rels = rels.replace(m.group(0), ""); mp = os.path.join(work, "word", m.group(1))
            if os.path.exists(mp): os.remove(mp)
    body = [block(HDR), block(GAME), block([tuple(x) for x in rep["subject"]])]
    if spec.get("timing"): body.append(para("Match Timing:", spec["timing"]))
    n = 0
    for s in rep["sections"]:
        body.append(para(s.get("label"), s["text"]))
        if s.get("diagram"):
            n += 1; png = s["diagram"] + ".png"; rid = f"rIdDiag{n}"
            shutil.copy(os.path.join(DD, png), os.path.join(work, "word/media", png))
            rels = rels.replace("</Relationships>", f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{png}"/></Relationships>')
            body.append(image(rid, 9000 + n, png))
    open(rp, "w", encoding="utf-8").write(rels)
    open(dp, "w", encoding="utf-8").write(head + "<w:body>" + "".join(body) + sect)
    ct = os.path.join(work, "[Content_Types].xml"); c = open(ct, encoding="utf-8").read()
    if 'Extension="png"' not in c:
        open(ct, "w", encoding="utf-8").write(c.replace("<Types ", "<Types ", 1).replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1))
    out = os.path.join(OUT, rep["filename"] + ".docx")
    if os.path.exists(out): os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(work):
            for f in files:
                full = os.path.join(root, f); z.write(full, os.path.relpath(full, work))
    shutil.rmtree(work)
    print(out, "pdf ok" if soffice_pdf(out, OUT) else "PDF CONVERSION FAILED")
    # plain text section
    plain.append("-" * 40); plain.append(rep["title"].upper())
    plain += [f"{a} {b}" for a, b in rep["subject"]]
    plain.append("")
    for s in rep["sections"]:
        plain.append((s["label"] + " " if s.get("label") else "") + s["text"]); plain.append("")

top = ["SUPPLEMENTAL REFEREE REPORT",
       f"Game {h['game_number']} | {h['date_time']} | {h['location']}", h["event"],
       f"Home: {h['home']}", f"Away: {h['away']}", f"Referee: {h['referee']}"]
if h.get("assistant_referees"): top.append(f"Assistant Referees: {h['assistant_referees']}")
if spec.get("timing"): top += ["", "MATCH TIMING", spec["timing"]]
txtp = os.path.join(OUT, f"{h['game_number']}_app.txt")
open(txtp, "w", encoding="utf-8").write("\n".join(top + [""] + plain).rstrip() + "\n")
print(txtp)
