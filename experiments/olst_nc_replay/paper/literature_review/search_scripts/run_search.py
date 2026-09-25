"""Run the search matrix against PubMed (E-utilities), Europe PMC, and arXiv.

Writes search_log.json with, per query and database: the verbatim query, the
UTC timestamp, the total hit count, and the top-N records (relevance-sorted
where the database supports it) with title / year / venue / identifiers /
abstract.
"""
import json, time, sys, re, html
import urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

sys.path.insert(0, ".")
from matrix import AXES, QUERIES

TOPN_PUBMED = 30
TOPN_EPMC = 25
TOPN_ARXIV = 15
UA = "olst-nc-litreview/1.0 (mailto:michaelryder.do@gmail.com)"


def get(url, retries=4, sleep=1.0):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa
            err = e
            time.sleep(sleep * (i + 1))
    raise RuntimeError(f"failed: {url} :: {err}")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------- PubMed ----------------
def pubmed(query):
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    q = urllib.parse.quote(query)
    js = json.loads(get(f"{base}esearch.fcgi?db=pubmed&term={q}&retmode=json&retmax={TOPN_PUBMED}&sort=relevance"))
    res = js["esearchresult"]
    count = int(res.get("count", 0))
    ids = res.get("idlist", [])
    records = []
    if ids:
        time.sleep(0.4)
        xmltxt = get(f"{base}efetch.fcgi?db=pubmed&id={','.join(ids)}&retmode=xml")
        root = ET.fromstring(xmltxt)
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
            abst = " ".join("".join(a.itertext()) for a in art.findall(".//Abstract/AbstractText"))
            journal = art.findtext(".//Journal/Title") or art.findtext(".//MedlineTA") or ""
            year = art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate") or ""
            doi = None
            pmc = None
            for aid in art.findall(".//ArticleIdList/ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = aid.text
                if aid.get("IdType") == "pmc":
                    pmc = aid.text
            authors = []
            for au in art.findall(".//AuthorList/Author")[:3]:
                ln = au.findtext("LastName") or au.findtext("CollectiveName") or ""
                authors.append(ln)
            records.append(dict(db="pubmed", pmid=pmid, pmc=pmc, doi=doi, title=title.strip(), year=year,
                                venue=journal, authors=authors, abstract=abst.strip()[:2500]))
    time.sleep(0.4)
    return count, records


# ---------------- Europe PMC ----------------
def epmc(query):
    q = urllib.parse.quote(query)
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&resultType=core&pageSize={TOPN_EPMC}"
    js = json.loads(get(url))
    count = int(js.get("hitCount", 0))
    records = []
    for r in js.get("resultList", {}).get("result", []):
        records.append(dict(db="epmc", pmid=r.get("pmid"), pmc=r.get("pmcid"), doi=r.get("doi"), epmc_id=r.get("id"),
                            source=r.get("source"), title=(r.get("title") or "").strip(), year=r.get("pubYear"),
                            venue=(r.get("journalInfo", {}).get("journal", {}).get("title") if r.get("journalInfo") else r.get("bookOrReportDetails", {}).get("publisher") if r.get("bookOrReportDetails") else None),
                            authors=[a.get("lastName", "") for a in (r.get("authorList", {}).get("author", []) or [])[:3]],
                            abstract=(r.get("abstractText") or "")[:2500]))
    time.sleep(0.5)
    return count, records


# ---------------- arXiv ----------------
def arxiv(query):
    q = urllib.parse.quote(query)
    url = f"https://export.arxiv.org/api/query?search_query={q}&max_results={TOPN_ARXIV}&sortBy=relevance"
    txt = get(url)
    ns = {"a": "http://www.w3.org/2005/Atom", "os": "http://a9.com/-/spec/opensearch/1.1/"}
    root = ET.fromstring(txt)
    count = int(root.findtext("os:totalResults", default="0", namespaces=ns) or 0)
    records = []
    for e in root.findall("a:entry", ns):
        aid = e.findtext("a:id", default="", namespaces=ns)
        records.append(dict(db="arxiv", arxiv_id=aid.rsplit("/", 1)[-1], doi=None,
                            title=re.sub(r"\s+", " ", e.findtext("a:title", default="", namespaces=ns)).strip(),
                            year=(e.findtext("a:published", default="", namespaces=ns) or "")[:4],
                            venue="arXiv",
                            authors=[a.findtext("a:name", default="", namespaces=ns).split()[-1] for a in e.findall("a:author", ns)[:3]],
                            abstract=re.sub(r"\s+", " ", e.findtext("a:summary", default="", namespaces=ns)).strip()[:2500]))
    time.sleep(3.0)  # arXiv asks for 3 s between requests
    return count, records


def main():
    import os
    args = sys.argv[1:]
    dbs = None
    if args and args[0] == "--db":
        dbs = args[1].split(","); args = args[2:]
    only = args
    outname = "search_log.json" if dbs is None else f"search_log_{'_'.join(dbs)}.json"
    log = dict(run_started=now(), axes=AXES, databases=dict(
        pubmed="NCBI E-utilities esearch (sort=relevance) + efetch; top %d" % TOPN_PUBMED,
        epmc="Europe PMC REST search, resultType=core, sort=relevance; top %d (includes preprints)" % TOPN_EPMC,
        arxiv="arXiv export API, sortBy=relevance; top %d" % TOPN_ARXIV,
    ), queries=[])
    for qd in QUERIES:
        if only and qd["id"] not in only:
            continue
        entry = dict(id=qd["id"], axis=qd["axis"], results={})
        for db, fn in (("pubmed", pubmed), ("epmc", epmc), ("arxiv", arxiv)):
            qs = qd.get(db)
            if not qs or (dbs and db not in dbs):
                continue
            t0 = now()
            try:
                count, recs = fn(qs)
                entry["results"][db] = dict(query=qs, timestamp=t0, count=count, records=recs)
                print(f"{qd['id']:6s} {db:7s} n={count:>7d} top={len(recs)}", flush=True)
            except Exception as e:
                entry["results"][db] = dict(query=qs, timestamp=t0, error=str(e))
                print(f"{qd['id']:6s} {db:7s} ERROR {e}", flush=True)
        log["queries"].append(entry)
        with open(outname, "w") as f:
            json.dump(log, f, indent=1)
    log["run_finished"] = now()
    with open(outname, "w") as f:
        json.dump(log, f, indent=1)


if __name__ == "__main__":
    main()
