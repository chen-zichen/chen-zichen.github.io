#!/usr/bin/env python3
"""Merge Google Scholar (which papers + venues) + arXiv (full authors, ids) + old repo (links, flags)
into site/publications/pubs.json. Scholar is the source of truth for the paper set."""
import json, re, sys
from pathlib import Path

S = Path(__file__).resolve().parent / "data"   # scholar.json + arxiv.json (fetched 2026-09-28)
OUT = Path(__file__).resolve().parents[2] / "site" / "publications" / "pubs.json"

scholar = json.loads((S / "scholar.json").read_text())
arxiv_raw = json.loads((S / "arxiv.json").read_text())
arxiv = {k.split("v")[0]: v for k, v in arxiv_raw.items()}  # strip version suffix

def ax(aid):
    return f"https://arxiv.org/abs/{aid}"

def scholar_by_prefix(prefix):
    hits = [s for s in scholar if s["title"].lower().startswith(prefix.lower())]
    assert len(hits) == 1, (prefix, hits)
    return hits[0]

# Curated entries, newest first within each year. `sp` = Scholar title prefix (identity check).
# authors: None -> take from arXiv; otherwise explicit (Scholar-only / old repo full names).
# date_precision="year": the curated date is a placeholder that only places the entry in the list (render_pubs.py
# then publishes just the year as datePublished); every other date is exact (arXiv or the proceedings page) -> "day".
E = [
  # ---------------- 2026 ----------------
  dict(id="acl2026-tasks-to-teams", sp="From tasks to teams",
       title="From Tasks to Teams: A Risk-First Evaluation Framework for Multi-Agent LLM Systems in Finance",
       authors=["Zichen Chen", "Jianda Chen", "Jiaao Chen", "Misha Sra"],
       venue_display="ACL 2026 · ICML 2025 Workshop on R2-FM",   # shown without "Findings"
       venue_full="Findings of the Association for Computational Linguistics: ACL 2026, 38819–38857; ICML 2025 Workshop on Reliable and Responsible Foundation Models (R2-FM)",
       group_year=2026, date="2026-05-01", date_precision="year",   # ordering key only: listed after the 2026 NeurIPS/COLM papers, above CoDA
       url="https://aclanthology.org/2026.findings-acl.1934/",
       notes=["oral."], arxiv_id=None),
  dict(id="arxiv2026-autolab", sp="AutoLab:", arxiv_id="2606.05080",
       title="AutoLab: Can Frontier Models Solve Long-Horizon Auto Research and Engineering Tasks?",
       venue_display="arXiv preprint", group_year=2026,
       page="https://autolab.moe/", code="https://github.com/autolabhq/autolab"),
  dict(id="arxiv2026-jobbench", sp="JobBench", arxiv_id="2605.26329",
       title="JobBench: Aligning Agent Work With Human Will",
       venue_display="NeurIPS 2026", venue_full="Advances in Neural Information Processing Systems (NeurIPS) 2026", group_year=2026),
  dict(id="arxiv2026-vab", sp="Visual Aesthetic Benchmark", arxiv_id="2605.12684",
       title="Visual Aesthetic Benchmark: Can Frontier Models Judge Beauty?",
       venue_display="COLM 2026", venue_full="Conference on Language Modeling (COLM) 2026", group_year=2026,
       page="https://vab.bakelab.ai/", code="https://github.com/BakeLab/Visual-Aesthetic-Benchmark"),
  dict(id="arxiv2026-narra-gym", sp="NARRA-Gym", arxiv_id="2605.08503",
       title="NARRA-Gym for Evaluating Interactive Narrative Agents",
       venue_display="NeurIPS 2026", venue_full="Advances in Neural Information Processing Systems (NeurIPS) 2026", group_year=2026),
  dict(id="iclr2026-coda", sp="CoDA:", arxiv_id="2510.03194",
       title="CoDA: Agentic Systems for Collaborative Data Visualization",
       # arXiv ASCII-fies the dotless i; the old repo spells the name correctly
       authors=["Zichen Chen", "Jiefeng Chen", "Sercan Ö. Arık", "Misha Sra", "Tomas Pfister", "Jinsung Yoon"],
       venue_display="ICLR 2026",
       venue_full="International Conference on Learning Representations (ICLR) 2026, 143276–143307",
       group_year=2026, date="2026-04-01", date_precision="year", page="https://coda-agent.github.io/CoDA/"),
  dict(id="arxiv2026-emergent-risks", sp="Emergent Social Intelligence Risks", arxiv_id="2603.27771",
       title="Emergent Social Intelligence Risks in Generative Multi-Agent Systems",
       venue_display="arXiv preprint", group_year=2026,
       page="https://howiehwong.github.io/blogs/MAS_risk.html"),
  # ---------------- 2025 ----------------
  dict(id="arxiv2025-personamem-v2", sp="Personamem-v2", arxiv_id="2512.06688",
       title="PersonaMem-v2: Towards Personalized Intelligence via Learning Implicit User Personas and Agentic Memory",
       venue_display="arXiv preprint", group_year=2025),
  dict(id="arxiv2025-industrynav", sp="Industrynav", arxiv_id="2511.17384",
       title="IndustryNav: Exploring Spatial Reasoning of Embodied Agents in Dynamic Industrial Navigation",
       venue_display="arXiv preprint", group_year=2025),
  dict(id="naacl2025-grapheval36k", sp="GraphEval36K", arxiv_id="2406.16176",
       title="GraphEval36K: Benchmarking Coding and Reasoning Capabilities of Large Language Models on Graph Datasets",
       equal_contrib=["Qiming Wu", "Zichen Chen"],
       venue_display="NAACL 2025",   # shown without "Findings"
       venue_full="Findings of the Association for Computational Linguistics: NAACL 2025, 8110–8132",
       group_year=2025, date="2025-04-01", date_precision="year", url="https://aclanthology.org/2025.findings-naacl.452/",
       page="https://grapheval36k.github.io/"),
  dict(id="arxiv2025-standard-benchmarks-fail", sp="Standard Benchmarks Fail", arxiv_id="2502.15865",
       title="Standard Benchmarks Fail — Auditing LLM Agents in Finance Must Prioritize Risk",
       venue_display="arXiv preprint", group_year=2025),
  dict(id="arxiv2025-agentic-workflows", sp="Agentic workflows", arxiv_id="2501.18002",
       title="Agentic Workflows for Conversational Human-AI Interaction Design",
       venue_display="arXiv preprint", group_year=2025),
  dict(id="arxiv2025-engaging-with-ai", sp="Engaging with AI", arxiv_id="2501.16627",
       title="Engaging with AI: How Interface Design Shapes Human-AI Collaboration in High-Stakes Decision-Making",
       venue_display="arXiv preprint", group_year=2025),
  # ---------------- 2024 ----------------
  dict(id="neurips2024-state-chrono", sp="State chrono", arxiv_id=None,
       title="State Chrono Representation for Enhancing Generalization in Reinforcement Learning",
       authors=["Jianda Chen", "Wen Zheng Terence Ng", "Zichen Chen", "Sinno Jialin Pan", "Tianwei Zhang"],
       venue_display="NeurIPS 2024",
       venue_full="Advances in Neural Information Processing Systems 37 (NeurIPS 2024), 73309–73336",
       group_year=2024, date="2024-12-01", date_precision="year",
       url="https://proceedings.neurips.cc/paper_files/paper/2024/hash/8600a9df1a087a9a66900cc8c948c3f0-Abstract-Conference.html"),
  dict(id="emnlp2024-xplainllm", sp="XplainLLM", arxiv_id="2311.08614",
       title="XplainLLM: A Knowledge-Augmented Dataset for Reliable Grounded Explanations in LLMs",
       venue_display="EMNLP 2024",
       venue_full="Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing (EMNLP 2024, Main), 7578–7596",
       group_year=2024, date="2024-11-01", date_precision="year", url="https://aclanthology.org/2024.emnlp-main.432/", code="https://github.com/chen-zichen/XplainLLM_dataset"),
  # ---------------- 2023 ----------------
  dict(id="ijcai2023-fedobd", sp="FedOBD", arxiv_id="2208.05174",
       title="FedOBD: Opportunistic Block Dropout for Efficiently Training Large-scale Neural Networks through Federated Learning",
       equal_contrib=["Yuanyuan Chen", "Zichen Chen"],
       venue_display="IJCAI 2023",
       venue_full="Proceedings of the Thirty-Second International Joint Conference on Artificial Intelligence (IJCAI-23), Main Track, 3541–3549",
       group_year=2023, date="2023-08-19", url="https://www.ijcai.org/proceedings/2023/394", notes=["oral."]),
  dict(id="arxiv2023-lmexplainer", sp="LMExplainer", arxiv_id="2303.16537",
       title="LMExplainer: Grounding Knowledge and Explaining Language Models",
       venue_display="arXiv preprint", group_year=2023),
  dict(id="iaai2023-fedobd-industrial", sp="Efficient Training of Large-scale Industrial", arxiv_id=None,
       title="Efficient Training of Large-scale Industrial Fault Diagnostic Models through Federated Opportunistic Block Dropout",
       authors=["Yuanyuan Chen", "Zichen Chen", "Sheng Guo", "Yansong Zhao", "Zelei Liu", "Pengcheng Wu",
                "Chengyi Yang", "Zengxiang Li", "Han Yu"],
       equal_contrib=["Yuanyuan Chen", "Zichen Chen", "Sheng Guo"],
       venue_display="AAAI/IAAI 2023",
       venue_full="Proceedings of the AAAI Conference on Artificial Intelligence 37(13), IAAI-23: 35th Annual Conference on Innovative Applications of Artificial Intelligence",
       group_year=2023, date="2023-02-01", date_precision="year", url="https://ojs.aaai.org/index.php/AAAI/article/view/26836",
       notes=["innovation award.", "oral."]),
  # ---------------- 2022 ----------------
  dict(id="ieeeaccess2022-map-segmentation", sp="Real-time hierarchical map", arxiv_id=None,
       title="Real-Time Hierarchical Map Segmentation for Coordinating Multirobot Exploration",
       authors=["Tianze Luo", "Zichen Chen", "Budhitama Subagdja", "Ah-Hwee Tan"],
       venue_display="IEEE Access", venue_full="IEEE Access 11, 15680–15692",
       group_year=2022, date="2022-07-01", date_precision="year", url="https://ieeexplore.ieee.org/abstract/document/9819930"),
  dict(id="hcii2022-flas", sp="FLAS:", arxiv_id=None,
       title="FLAS: A Platform for Studying Attacks on Federated Learning",
       authors=["Yuanchao Loh", "Zichen Chen", "Yansong Zhao", "Han Yu"],
       venue_display="HCII 2022 (SCSM)",
       venue_full="International Conference on Human-Computer Interaction (HCII 2022), Social Computing and Social Media: Design, User Experience and Impact, 160–169",
       group_year=2022, date="2022-06-01", date_precision="year", url="https://link.springer.com/chapter/10.1007/978-3-031-05061-9_12"),
  # ---------------- 2020 ----------------
  dict(id="book2020-gamified-incentive-tool", sp="A gamified research tool", arxiv_id=None,
       title="A Gamified Research Tool for Incentive Mechanism Design in Federated Learning",
       authors=["Zichen Chen", "Zelei Liu", "Kang Loon Ng", "Han Yu", "Yang Liu", "Qiang Yang"],
       venue_display="Book chapter, in Federated Learning: Privacy and Incentive",
       venue_full="Federated Learning: Privacy and Incentive (Springer), 168–175",
       group_year=2020, date="2020-11-26", url="https://link.springer.com/chapter/10.1007/978-3-030-63076-8_12"),
  # IJCAI-PRICAI 2020 = the 29th IJCAI (held Jan 2021); Crossref 10.24963/ijcai.2020/769, ijcai.org: Demos track, 2020/07/09.
  # The old page said "IJCAI 2021" (that is the 30th conference). Rule 5: the venue names 2020 -> group 2020.
  dict(id="ijcai2020-fl-incentive-game", sp="A multi-player game", arxiv_id=None,
       title="A Multi-player Game for Studying Federated Learning Incentive Schemes",
       authors=["Kang Loon Ng", "Zichen Chen", "Zelei Liu", "Han Yu", "Yang Liu", "Qiang Yang"],
       venue_display="IJCAI-PRICAI 2020",   # year follows Scholar (2021; the conference met in Jan 2021); no track qualifier
       venue_full="Proceedings of the Twenty-Ninth International Joint Conference on Artificial Intelligence (IJCAI-PRICAI 2020), Demos track, 5279–5281",
       group_year=2021, date="2021-01-07", url="https://www.ijcai.org/proceedings/2020/769",
       notes=["oral."]),
  # ---------------- 2019 ----------------
  dict(id="ica2019-multiagent-drl", sp="End-to-end deep reinforcement", arxiv_id=None,
       title="End-to-end Deep Reinforcement Learning for Multi-agent Collaborative Exploration",
       authors=["Zichen Chen", "Budhitama Subagdja", "Ah-Hwee Tan"],
       venue_display="IEEE ICA 2019",
       venue_full="2019 IEEE International Conference on Agents (ICA), 99–102",
       group_year=2019, date="2019-10-01", date_precision="year", url="https://ieeexplore.ieee.org/abstract/document/8929192",
       notes=["oral."]),
]

# One spelling per person across the page (arXiv records disagree: "Ambuj Singh" / "Ambuj K Singh" / "Ambuj K. Singh").
NAME_FIX = {"Ambuj Singh": "Ambuj K. Singh", "Ambuj K Singh": "Ambuj K. Singh", "Nitesh V Chawla": "Nitesh V. Chawla"}

def initials_ok(full, short):
    """Scholar 'AK Singh' / 'WZT Ng' vs full name: surname equal and initials consistent."""
    fp, sp = full.replace("-", " ").replace(".", "").split(), short.replace("*", "").split()
    if fp[-1].lower().replace("ı", "i") != sp[-1].lower().replace("ı", "i"):
        return False
    ini = "".join(p[0] for p in fp[:-1]).upper()
    return ini.startswith(sp[0]) or sp[0].startswith(ini[:1])

out, seen = [], set()
for e in E:
    s = scholar_by_prefix(e["sp"])
    assert id(s) not in seen; seen.add(id(s))
    aid = e.get("arxiv_id")
    a = arxiv.get(aid) if aid else None
    if aid: assert a, aid
    authors = e.get("authors") or (a["authors"] if a else None)
    assert authors, e["id"]
    authors = [NAME_FIX.get(x, x) for x in authors]
    # check against Scholar's (possibly truncated) list
    sch = [x.strip() for x in s["authors"].split(",")]
    trunc = sch and sch[-1] == "..."
    sch = [x for x in sch if x != "..."]
    for i, x in enumerate(sch):
        assert initials_ok(authors[i], x), (e["id"], authors[i], x)
    if not trunc:
        assert len(sch) == len(authors), (e["id"], len(sch), len(authors))
    star = [authors[i] for i, x in enumerate(sch) if x.endswith("*")]
    eq = [NAME_FIX.get(x, x) for x in e.get("equal_contrib", star)]
    assert set(star) <= set(eq), (e["id"], star, eq)
    date = e.get("date") or (a["published"] if a else None)
    assert date, e["id"]
    venue_full = e.get("venue_full") or (f"arXiv preprint arXiv:{aid}" if aid else None)
    prec = e.get("date_precision", "day")
    assert prec in ("day", "year"), (e["id"], prec)
    out.append({
        "id": e["id"],
        "title": e["title"],
        "authors": authors,
        "equal_contrib": eq,
        "venue_display": e["venue_display"],
        "venue_full": venue_full,
        "group_year": e["group_year"],
        "date": date,
        "date_precision": prec,
        "url": e.get("url") or ax(aid),
        "page": e.get("page"),
        "code": e.get("code"),
        "notes": e.get("notes", []),
        "scholar_title": s["title"],
        "arxiv_id": aid,
    })

# Added manually, not on Google Scholar yet (2026-09-28). No Scholar identity check for these.
EXTRA = [
  dict(id="arxiv2026-reward-hacking", arxiv_id="2609.28614",
       title="Reward Hacking Challenges Oversight of Autonomous Research Agents",
       venue_display="arXiv preprint", group_year=2026),
  # Bake AI Research blog post; canonical bakeai.inc URL (a workers.dev preview mirrors the same page).
  dict(id="bakeai2026-epi", arxiv_id=None,
       title="Épi: Turning Compute into Verifiable Improvement",   # title-cased to match the list (the post itself uses sentence case)
       authors=["Epi Team"],   # as in the post's own citation
       venue_display="Bake AI Research", venue_full="Bake AI Research (BakeLab), research article",
       group_year=2026, date="2026-09-12", url="https://bakeai.inc/research/articles/epi/"),
]
for e in EXTRA:
    aid = e.get("arxiv_id")
    a = arxiv.get(aid) if aid else None
    if aid: assert a, aid
    authors = [NAME_FIX.get(x, x) for x in (e.get("authors") or a["authors"])]
    date = e.get("date") or a["published"]
    out.append({
        "id": e["id"], "title": e["title"], "authors": authors, "equal_contrib": e.get("equal_contrib", []),
        "venue_display": e["venue_display"],
        "venue_full": e.get("venue_full") or f"arXiv preprint arXiv:{aid}",
        "group_year": e["group_year"], "date": date, "date_precision": e.get("date_precision", "day"),
        "url": e.get("url") or ax(aid), "page": e.get("page"), "code": e.get("code"),
        "notes": e.get("notes", []), "scholar_title": None, "arxiv_id": aid,
    })

assert len(out) == len(scholar) + len(EXTRA), (len(out), len(scholar))
assert len(seen) == len(scholar)
# ordering: group_year desc, then date desc
out.sort(key=lambda p: (p["group_year"], p["date"]), reverse=True)
keys = [(p["group_year"], p["date"]) for p in out]
assert keys == sorted(keys, reverse=True), keys
assert len({p["id"] for p in out}) == len(out)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print("wrote", OUT, len(out))
