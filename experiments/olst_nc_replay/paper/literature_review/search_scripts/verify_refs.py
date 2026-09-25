"""Resolve every intended reference to a verified identifier + metadata.
PubMed: by PMID, else by DOI, else by title words in [ti] (+year).
Crossref: by DOI or bibliographic query (top hit, with title check).
arXiv: by id. Europe PMC: by DOI.
Writes verified_refs.json; prints anything unresolved or with a weak title match.
"""
import json, re, sys, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
sys.path.insert(0, ".")
from refs_to_verify import REFS
UA = {"User-Agent": "olst-nc-litreview/1.0 (mailto:michaelryder.do@gmail.com)"}

def get(url, data=None):
    for i in range(4):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        except Exception as e:
            err = e; time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url}: {err}")

def norm(s): return re.sub(r"[^a-z0-9 ]", "", (s or "").lower())

def pubmed_fetch(pmids):
    xml = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", data=urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}).encode())
    out = {}
    for art in ET.fromstring(xml).findall(".//PubmedArticle"):
        pmid = art.findtext("./MedlineCitation/PMID")
        a = art.find("./MedlineCitation/Article")
        title = "".join(a.find("ArticleTitle").itertext()).strip()
        journal = a.findtext("./Journal/Title"); iso = a.findtext("./Journal/ISOAbbreviation")
        year = a.findtext("./Journal/JournalIssue/PubDate/Year") or (a.findtext("./Journal/JournalIssue/PubDate/MedlineDate") or "")[:4]
        vol = a.findtext("./Journal/JournalIssue/Volume"); issue = a.findtext("./Journal/JournalIssue/Issue")
        pages = a.findtext("./Pagination/MedlinePgn")
        doi = pmc = None
        for aid in art.findall("./PubmedData/ArticleIdList/ArticleId"):
            if aid.get("IdType") == "doi": doi = aid.text
            if aid.get("IdType") == "pmc": pmc = aid.text
        authors = []
        for au in a.findall("./AuthorList/Author"):
            ln = au.findtext("LastName"); ini = au.findtext("Initials"); cn = au.findtext("CollectiveName")
            if ln: authors.append(f"{ln}, {ini or ''}".strip(", "))
            elif cn: authors.append(cn)
        abstract = " ".join("".join(x.itertext()) for x in a.findall("./Abstract/AbstractText"))
        out[pmid] = dict(pmid=pmid, doi=doi, pmc=pmc, title=title, journal=journal, journal_abbrev=iso, year=year, volume=vol, issue=issue, pages=pages, authors=authors, abstract=abstract[:1200])
    return out

def pubmed_search(term):
    js = json.loads(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "term": term, "retmode": "json", "retmax": 5})))
    return js["esearchresult"].get("idlist", [])

def crossref_doi(doi):
    js = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(doi)))
    return js["message"]

def crossref_query(q):
    js = json.loads(get("https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": q, "rows": 3})))
    return js["message"]["items"]

def cr_to_rec(m):
    yr = None
    for k in ("published-print", "published-online", "issued", "created"):
        if m.get(k, {}).get("date-parts"): yr = m[k]["date-parts"][0][0]; break
    return dict(doi=m.get("DOI"), title=(m.get("title") or [""])[0], journal=(m.get("container-title") or [""])[0], year=str(yr) if yr else None,
                volume=m.get("volume"), issue=m.get("issue"), pages=m.get("page"),
                authors=[f"{a.get('family','')}, {a.get('given','')}".strip(", ") for a in m.get("author", [])], type=m.get("type"))

def arxiv_rec(aid):
    txt = get(f"https://export.arxiv.org/api/query?id_list={aid}")
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = ET.fromstring(txt).find("a:entry", ns)
    time.sleep(3)
    return dict(arxiv=aid, title=re.sub(r"\s+", " ", e.findtext("a:title", namespaces=ns)).strip(), year=e.findtext("a:published", namespaces=ns)[:4],
                published=e.findtext("a:published", namespaces=ns)[:10], authors=[a.findtext("a:name", namespaces=ns) for a in e.findall("a:author", ns)],
                doi=e.findtext("{http://arxiv.org/schemas/atom}doi"), journal_ref=e.findtext("{http://arxiv.org/schemas/atom}journal_ref"),
                abstract=re.sub(r"\s+", " ", e.findtext("a:summary", namespaces=ns)).strip()[:1200])

def epmc_doi(doi):
    js = json.loads(get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": f'DOI:"{doi}"', "format": "json", "resultType": "core"})))
    r = js["resultList"]["result"][0]
    return dict(doi=r.get("doi"), pmid=r.get("pmid"), title=r.get("title"), year=r.get("pubYear"), source=r.get("source"),
                journal=(r.get("journalInfo", {}).get("journal", {}).get("title") if r.get("journalInfo") else r.get("bookOrReportDetails", {}).get("publisher")),
                authors=[f"{a.get('lastName','')}, {a.get('initials','')}".strip(", ") for a in r.get("authorList", {}).get("author", [])],
                abstract=(r.get("abstractText") or "")[:1200], firstPublicationDate=r.get("firstPublicationDate"))

out = {}; problems = []
for key, title, year, hint, kind in REFS:
    rec = None; how = None
    try:
        if kind == "pubmed":
            ids = []
            if hint.get("pmid"): ids = [hint["pmid"]]; how = "pmid"
            elif hint.get("doi"): ids = pubmed_search(f'{hint["doi"]}[doi]'); how = "doi"
            if not ids:
                words = [w for w in re.findall(r"[A-Za-z0-9\-']+", title) if len(w) > 2][:10]
                term = " AND ".join(f"{w}[ti]" for w in words) + (f" AND {year}[dp]" if year else "")
                ids = pubmed_search(term); how = "title"
                if not ids and year:
                    term = " AND ".join(f"{w}[ti]" for w in words); ids = pubmed_search(term); how = "title-noyear"
            time.sleep(0.4)
            if ids:
                recs = pubmed_fetch(ids[:1]); rec = list(recs.values())[0]; time.sleep(0.4)
        elif kind == "crossref":
            if hint.get("doi"): rec = cr_to_rec(crossref_doi(hint["doi"])); how = "doi"
            else:
                items = crossref_query(hint.get("query") or title); rec = cr_to_rec(items[0]) if items else None; how = "query"
            time.sleep(0.5)
        elif kind == "arxiv":
            rec = arxiv_rec(hint["arxiv"]); how = "arxiv"
        elif kind == "epmc":
            rec = epmc_doi(hint["doi"]); how = "epmc-doi"
    except Exception as e:
        problems.append((key, f"ERROR {e}")); continue
    if not rec:
        problems.append((key, "UNRESOLVED")); continue
    # title check
    tn = norm(title); rn = norm(rec.get("title"))
    ok = all(w in rn for w in tn.split()[:4]) or (len(tn) > 0 and tn[:25] in rn)
    rec["_bibkey"] = key; rec["_expected_title"] = title; rec["_resolved_by"] = how; rec["_title_match"] = ok
    out[key] = rec
    flag = "" if ok else "   <-- CHECK TITLE"
    print(f"{key:24s} {how:12s} {rec.get('year')} | {rec.get('title')[:90]}{flag}")
json.dump(out, open("verified_refs.json", "w"), indent=1)
print("\nPROBLEMS:"); [print(p) for p in problems]
