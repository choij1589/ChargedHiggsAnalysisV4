#!/usr/bin/env python3
"""Compare two SKNano output files object by object (docs/PLAN_Optimization.md, Validation).

What it checks (REF = reference build, NEW = build under test, same input files):

* Object set: every key (directories walked recursively, latest cycle) present in both files with the
  same class. Objects only in one file are differences unless matched by an ``ignore`` rule.
* Histograms (TH1*/TH2*/TH3*, TProfile*): axis binning per axis (number of bins, edges, bin labels),
  bin contents and bin errors of every bin incl. under/overflow, fEntries and the statistics sums
  (fTsumw, fTsumw2, fTsumwx, fTsumwx2), for profiles also fBinEntries / fBinSumw2. Titles: a warning.
* RNTuples (``ROOT::RNTuple``): the same top-level field set and field types, the same entry count,
  then every field entry by entry. Entries are compared in file order when the event key
  (default ``run, lumi, event``) is identical in both files in the same order; otherwise they are
  matched on the key (k-th occurrence of a duplicated key matched to the k-th; unmatched keys
  reported). Vectors (``std::vector<T>``, nested) elementwise after their lengths; floats exact by
  default (NaN == NaN), integers and bools always exact unless a rule gives a tolerance.
  In-order mode reads ``--chunk-size`` entries at a time (memory bounded by the chunk, not by the
  RNTuple); key-matched mode reads one field at a time.
* RNTuple storage (information, never a difference): on-disk (compressed) and uncompressed bytes,
  clusters, compression algorithm and level of the pages (e.g. LZ4-4 = 404, ZSTD-5 = 505) and the
  column encodings (Real32 / Real32Quant / Real16 ...) per RNTuple, REF vs NEW.

Tolerances: a value pair (a, b) passes if a == b, both are NaN, or |a - b| <= max(abs, rel x max(|a|, |b|)).
``--tol-rel`` / ``--tol-abs`` apply to all floating-point values; ``--allow PATTERN=TOL`` (repeatable,
first match wins) overrides them for the objects / fields whose name matches the glob PATTERN
(``fnmatch``, ``*`` also matches ``/``). Names are the object path for histograms and objects
(``ElFR/Ele12/QCD/loose/Nom/data/pt``) and ``<rntuple path>:<field>`` for RNTuple fields
(``SR_3MU_Central:lep_eta``). TOL is ``1e-6`` (relative), ``rel:1e-6``, ``abs:1e-4``,
``abs:1e-4,rel:1e-3`` or ``ignore`` (the object / field is skipped, also when it exists in one file
only, e.g. ``--allow 'Train_*:prescale=ignore'``). A rule tolerance applies to integer fields too.

Output: per object the first ``--max-report`` differences (bin / entry, event key, REF and NEW values),
per field / histogram the number of differing bins / entries and the largest absolute / relative
difference, summary counts (identical, equal within tolerance, different), the storage table, and
optionally everything as JSON (``--json``). Exit code 0 only if both files are identical within the
tolerances, 1 if they differ, 2 on a read error.

Requires uproot >= 5.7 (RNTuple reading), awkward, numpy (the NanoV15 environment); no ROOT.

Usage:
    compare_outputs.py REF.root NEW.root [--tol-rel X] [--tol-abs X] [--allow PATTERN=TOL ...]
                       [--key run,lumi,event] [--chunk-size N] [--max-report N] [--only GLOB ...]
                       [--skip GLOB ...] [--quiet] [--json out.json]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import math
import sys
import time

import numpy as np

try:
    import awkward as ak
    import uproot
except ImportError as exc:  # pragma: no cover
    sys.exit(f"compare_outputs.py needs uproot and awkward (NanoV15 environment): {exc}")

COMPRESSION_ALGOS = {0: "inherit", 1: "ZLIB", 2: "LZMA", 3: "OLD", 4: "LZ4", 5: "ZSTD"}
# RNTuple on-disk column types (ROOT ENTupleColumnType; names as in RNTuple spec 1.0)
COLUMN_TYPES = {
    0: "Bit", 1: "Byte", 2: "Char", 3: "Int8", 4: "UInt8", 5: "Int16", 6: "UInt16", 7: "Int32",
    8: "UInt32", 9: "Int64", 10: "UInt64", 11: "Real16", 12: "Real32", 13: "Real64", 14: "Index32",
    15: "Index64", 16: "Switch", 17: "SplitInt16", 18: "SplitUInt16", 19: "SplitInt32",
    20: "SplitUInt32", 21: "SplitInt64", 22: "SplitUInt64", 23: "SplitReal16", 24: "SplitReal32",
    25: "SplitReal64", 26: "SplitIndex32", 27: "SplitIndex64", 28: "Real32Trunc", 29: "Real32Quant",
}
HIST_PREFIXES = ("TH1", "TH2", "TH3", "TProfile")
STAT_MEMBERS = ("fEntries", "fTsumw", "fTsumw2", "fTsumwx", "fTsumwx2", "fTsumwy", "fTsumwy2",
                "fTsumwxy", "fTsumwz", "fTsumwz2", "fTsumwxz", "fTsumwyz")


# ----------------------------------------------------------------------------------------------
# tolerances
class Tol:
    """Tolerance of one object / field: exact, abs/rel, or ignored."""

    __slots__ = ("abs", "rel", "ignore", "source")

    def __init__(self, abs_=0.0, rel=0.0, ignore=False, source="default"):
        self.abs, self.rel, self.ignore, self.source = float(abs_), float(rel), ignore, source

    @property
    def exact(self):
        return self.abs == 0.0 and self.rel == 0.0

    def describe(self):
        if self.ignore:
            return "ignore"
        if self.exact:
            return "exact"
        parts = []
        if self.abs:
            parts.append(f"abs {self.abs:g}")
        if self.rel:
            parts.append(f"rel {self.rel:g}")
        return ", ".join(parts)


def parse_tol(text, source):
    text = text.strip()
    if text.lower() == "ignore":
        return Tol(ignore=True, source=source)
    abs_, rel = 0.0, 0.0
    for part in text.split(","):
        part = part.strip()
        if ":" in part:
            kind, val = part.split(":", 1)
            kind = kind.strip().lower()
            if kind == "abs":
                abs_ = float(val)
            elif kind == "rel":
                rel = float(val)
            else:
                raise ValueError(f"unknown tolerance kind '{kind}' in '{text}'")
        else:
            rel = float(part)
    return Tol(abs_, rel, source=source)


class Rules:
    def __init__(self, allow, tol_abs, tol_rel):
        self.rules = []
        for item in allow or []:
            if "=" not in item:
                raise ValueError(f"--allow needs PATTERN=TOL, got '{item}'")
            pat, tol = item.rsplit("=", 1)
            self.rules.append((pat, parse_tol(tol, f"--allow {item}")))
        self.default = Tol(tol_abs, tol_rel, source="--tol-abs/--tol-rel")
        self.exact = Tol(source="exact")

    def for_name(self, name, integer=False):
        for pat, tol in self.rules:
            if fnmatch.fnmatchcase(name, pat):
                return tol
        return self.exact if integer else self.default


# ----------------------------------------------------------------------------------------------
# value comparison
def _as_f64(x):
    return np.asarray(x, dtype=np.float64)


def compare_arrays(a, b, tol):
    """Elementwise comparison of two equally shaped numeric / bool arrays.

    Returns (bad, n_inexact, max_abs, max_rel): bad = mask of pairs beyond the tolerance, n_inexact =
    pairs that are not exactly equal (incl. those within tolerance)."""
    a = np.asarray(a)
    b = np.asarray(b)
    if a.dtype == np.bool_ or b.dtype == np.bool_:
        ne = a.astype(bool) != b.astype(bool)
        return ne, int(ne.sum()), float(ne.any()), float(ne.any())
    floating = np.issubdtype(a.dtype, np.floating) or np.issubdtype(b.dtype, np.floating)
    if floating:
        fa, fb = _as_f64(a), _as_f64(b)
        nan_a, nan_b = np.isnan(fa), np.isnan(fb)
        with np.errstate(invalid="ignore"):
            eq = (fa == fb) | (nan_a & nan_b)
        ne = ~eq
        n_inexact = int(ne.sum())
        if not n_inexact:
            return ne, 0, 0.0, 0.0
        with np.errstate(invalid="ignore", over="ignore"):
            diff = np.abs(fa - fb)
            scale = np.maximum(np.abs(fa), np.abs(fb))
            rel = np.where(scale > 0, diff / np.where(scale > 0, scale, 1.0), 0.0)
        diff = np.where(ne, diff, 0.0)
        rel = np.where(ne, rel, 0.0)
        one_nan = nan_a ^ nan_b
        if tol.exact:
            bad = ne
        else:
            with np.errstate(invalid="ignore"):
                bad = ne & ~(diff <= np.maximum(tol.abs, tol.rel * scale))
        bad = bad | one_nan
        finite = ne & ~one_nan & np.isfinite(diff)
        max_abs = float(diff[finite].max()) if finite.any() else (math.inf if one_nan.any() else 0.0)
        max_rel = float(rel[finite].max()) if finite.any() else (math.inf if one_nan.any() else 0.0)
        if one_nan.any():
            max_abs, max_rel = math.inf, math.inf
        return bad, n_inexact, max_abs, max_rel
    # integers: exact unless a rule gives a tolerance
    ia = a.astype(np.int64) if a.dtype != np.uint64 else a
    ib = b.astype(np.int64) if b.dtype != np.uint64 else b
    ne = ia != ib
    n_inexact = int(ne.sum())
    if not n_inexact:
        return ne, 0, 0.0, 0.0
    fa, fb = _as_f64(ia), _as_f64(ib)
    diff = np.abs(fa - fb)
    scale = np.maximum(np.abs(fa), np.abs(fb))
    rel = np.where(scale > 0, diff / np.where(scale > 0, scale, 1.0), 0.0)
    bad = ne if tol.exact else ne & ~(diff <= np.maximum(tol.abs, tol.rel * scale))
    return bad, n_inexact, float(diff.max()), float(rel.max())


def _py(v):
    """JSON-friendly scalar."""
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        v = float(v)
        if math.isnan(v) or math.isinf(v):
            return repr(v)
        return v
    return v


# ----------------------------------------------------------------------------------------------
# file walking
def list_objects(f):
    """{path: classname} of all non-directory objects (latest cycle) and the set of directories."""
    objects, dirs = {}, set()
    for path, cls in f.classnames(recursive=True, cycle=False).items():
        if cls == "TDirectory" or cls == "TDirectoryFile":
            dirs.add(path)
        else:
            objects[path] = cls
    return objects, dirs


def selected(path, only, skip):
    if only and not any(fnmatch.fnmatchcase(path, p) for p in only):
        return False
    if skip and any(fnmatch.fnmatchcase(path, p) for p in skip):
        return False
    return True


# ----------------------------------------------------------------------------------------------
# histograms
def _axis_info(h, i):
    ax = h.axes[i]
    edges = np.asarray(ax.edges(flow=False), dtype=np.float64)
    try:
        labels = ax.labels()
    except Exception:  # pragma: no cover
        labels = None
    return edges, (list(labels) if labels else None)


def _bin_desc(h, flat_index, shape):
    """Human-readable bin description of a flat index into values(flow=True)."""
    idx = np.unravel_index(flat_index, shape)
    parts = []
    for d, i in enumerate(idx):
        n = shape[d] - 2
        if i == 0:
            parts.append("underflow")
        elif i == n + 1:
            parts.append("overflow")
        else:
            edges = np.asarray(h.axes[d].edges(flow=False))
            parts.append(f"bin {i} [{edges[i - 1]:g}, {edges[i]:g})")
    return ", ".join(parts)


def compare_hist(path, hr, hn, tol, max_report):
    res = {"type": "histogram", "class": hr.classname, "status": "identical", "issues": [],
           "tolerance": tol.describe()}
    issues = res["issues"]
    ndim = len(hr.axes)
    if len(hn.axes) != ndim:
        issues.append({"what": "dimension", "ref": ndim, "new": len(hn.axes)})
        res["status"] = "different"
        return res
    for d in range(ndim):
        er, lr = _axis_info(hr, d)
        en, ln = _axis_info(hn, d)
        if er.shape != en.shape or not np.array_equal(er, en):
            issues.append({"what": f"axis {d} binning", "ref": f"{len(er) - 1} bins [{er[0]:g}, {er[-1]:g}]",
                           "new": f"{len(en) - 1} bins [{en[0]:g}, {en[-1]:g}]"})
        if lr != ln:
            issues.append({"what": f"axis {d} labels", "ref": lr, "new": ln})
    if issues:
        res["status"] = "different"
        return res
    if hr.member("fTitle") != hn.member("fTitle"):
        res["warnings"] = [{"what": "title", "ref": hr.member("fTitle"), "new": hn.member("fTitle")}]
    inexact = 0
    arrays = [("content", hr.values(flow=True), hn.values(flow=True)),
              ("error", np.sqrt(np.abs(hr.variances(flow=True))), np.sqrt(np.abs(hn.variances(flow=True))))]
    if hr.classname.startswith("TProfile"):
        for m in ("fBinEntries", "fBinSumw2"):
            try:
                arrays.append((m, np.asarray(hr.member(m)), np.asarray(hn.member(m))))
            except Exception:
                pass
    shape = np.shape(arrays[0][1])
    res["integral_ref"] = float(np.sum(arrays[0][1]))
    res["integral_new"] = float(np.sum(arrays[0][2]))
    for what, a, b in arrays:
        a = np.asarray(a).ravel()
        b = np.asarray(b).ravel()
        if a.shape != b.shape:
            issues.append({"what": what, "ref": f"{a.size} cells", "new": f"{b.size} cells"})
            continue
        bad, n_in, mabs, mrel = compare_arrays(a, b, tol)
        inexact += n_in
        if bad.any():
            first = np.flatnonzero(bad)[:max_report]
            issues.append({
                "what": what, "n_bins": int(bad.sum()), "n_cells": int(a.size), "max_abs": mabs,
                "max_rel": mrel,
                "first": [{"bin": _bin_desc(hr, int(i), shape) if len(shape) == ndim else int(i),
                           "ref": _py(a[i]), "new": _py(b[i])} for i in first]})
        elif n_in:
            res.setdefault("within_tolerance", []).append(
                {"what": what, "n_bins": n_in, "max_abs": mabs, "max_rel": mrel})
    for m in STAT_MEMBERS:
        try:
            a, b = hr.member(m), hn.member(m)
        except Exception:
            continue
        bad, n_in, mabs, mrel = compare_arrays(np.array([a]), np.array([b]), tol)
        inexact += n_in
        if bad.any():
            issues.append({"what": m, "ref": _py(a), "new": _py(b), "max_abs": mabs, "max_rel": mrel})
    if issues:
        res["status"] = "different"
    elif inexact:
        res["status"] = "within_tolerance"
    return res


def compare_other(path, r, n):
    """Objects that are neither histograms nor RNTuples: compare their streamed members."""
    def members(o):
        try:
            mem = o.all_members
        except Exception:
            return repr(o)
        return {k: repr(v) for k, v in mem.items() if k not in ("@fUniqueID", "@fBits")}
    mr, mn = members(r), members(n)
    if mr == mn:
        return {"type": "object", "status": "identical", "issues": []}
    keys = sorted(set(mr) | set(mn)) if isinstance(mr, dict) and isinstance(mn, dict) else ["repr"]
    issues = []
    for k in keys:
        a = mr.get(k) if isinstance(mr, dict) else mr
        b = mn.get(k) if isinstance(mn, dict) else mn
        if a != b:
            issues.append({"what": k, "ref": str(a)[:200], "new": str(b)[:200]})
    return {"type": "object", "status": "different", "issues": issues}


# ----------------------------------------------------------------------------------------------
# RNTuples
def rntuple_fields(o):
    """Top-level fields: {name: type_name} in field order."""
    recs = o.field_records
    out = {}
    for i, rec in enumerate(recs):
        if rec.parent_field_id == i:
            out[rec.field_name] = rec.type_name
    return out


def rntuple_storage(o):
    """On-disk size, compression settings and column encodings of one RNTuple."""
    recs = o.field_records
    cols = o.column_records

    def top(fid):
        seen = 0
        while recs[fid].parent_field_id != fid and seen < 1000:
            fid = recs[fid].parent_field_id
            seen += 1
        return recs[fid].field_name

    col_top = [top(c.field_id) for c in cols]
    comp_bytes, raw_bytes, settings = 0, 0.0, set()
    per_field = {}
    n_clusters = 0
    for group in o.page_link_list:
        n_clusters += 1
        for ic, cp in enumerate(group):
            if getattr(cp, "suppressed", False) or ic >= len(cols):
                continue
            settings.add(int(cp.compression_settings))
            nb = sum(p.locator.num_bytes for p in cp.pages)
            ne = sum(p.num_elements for p in cp.pages)
            raw = ne * cols[ic].nbits / 8.0
            comp_bytes += nb
            raw_bytes += raw
            f = per_field.setdefault(col_top[ic], [0, 0.0])
            f[0] += nb
            f[1] += raw
    enc = {}
    for ic, c in enumerate(cols):
        name = COLUMN_TYPES.get(c.type, str(c.type))
        if name in ("Index32", "Index64", "SplitIndex32", "SplitIndex64", "Switch"):
            continue
        enc.setdefault(col_top[ic], set()).add(f"{name}" + (f"({c.nbits})" if name == "Real32Quant" else ""))
    return {
        "entries": int(o.num_entries),
        "clusters": n_clusters,
        "bytes_on_disk": int(comp_bytes),
        "bytes_uncompressed": int(raw_bytes),
        "compression": sorted(settings),
        "compression_names": [f"{COMPRESSION_ALGOS.get(s // 100, s // 100)}-{s % 100}" for s in sorted(settings)],
        "field_bytes_on_disk": {k: int(v[0]) for k, v in sorted(per_field.items(), key=lambda kv: -kv[1][0])},
        "encodings": {k: sorted(v) for k, v in enc.items()},
    }


def _is_list(arr):
    t = arr.type.content if hasattr(arr.type, "content") else arr.type
    return isinstance(t, (ak.types.ListType, ak.types.RegularType))


def _is_record(arr):
    t = arr.type.content if hasattr(arr.type, "content") else arr.type
    return isinstance(t, ak.types.RecordType)


class FieldStats:
    def __init__(self, name, tol):
        self.name, self.tol = name, tol
        self.bad_entries = 0
        self.inexact = 0
        self.length_mismatch = 0
        self.max_abs = 0.0
        self.max_rel = 0.0
        self.first = []

    def as_dict(self):
        d = {"field": self.name, "tolerance": self.tol.describe(), "entries_beyond_tol": self.bad_entries,
             "values_not_exact": self.inexact, "length_mismatch": self.length_mismatch,
             "max_abs": self.max_abs, "max_rel": self.max_rel, "first": self.first}
        return d


def compare_values(a, b, entry_ref, entry_new, keyfn, st, max_report):
    """Compare one field chunk (awkward arrays of equal length). entry_ref / entry_new: numpy entry
    numbers of the rows (for the report). Recurses into lists and records."""
    if _is_record(a):
        for fld in a.fields:
            if fld in b.fields:
                compare_values(a[fld], b[fld], entry_ref, entry_new, keyfn, st, max_report)
        return
    if _is_list(a):
        na = ak.to_numpy(ak.num(a, axis=1))
        nb = ak.to_numpy(ak.num(b, axis=1))
        lm = na != nb
        if lm.any():
            st.length_mismatch += int(lm.sum())
            st.bad_entries += int(lm.sum())
            for i in np.flatnonzero(lm):
                if len(st.first) >= max_report:
                    break
                st.first.append({"entry": int(entry_ref[i]), "entry_new": int(entry_new[i]),
                                 "key": keyfn(i), "what": "length", "ref": int(na[i]), "new": int(nb[i])})
            keep = ~lm
            a, b, na = a[keep], b[keep], na[keep]
            entry_ref, entry_new = entry_ref[keep], entry_new[keep]
            keep_idx = np.flatnonzero(keep)
            keyfn_inner = (lambda j, _k=keyfn, _m=keep_idx: _k(_m[j]))
        else:
            keyfn_inner = keyfn
        fa, fb = ak.flatten(a, axis=1), ak.flatten(b, axis=1)
        compare_values(fa, fb, np.repeat(entry_ref, na), np.repeat(entry_new, na),
                       (lambda j, _k=keyfn_inner, _o=np.repeat(np.arange(len(na)), na): _k(_o[j])),
                       st, max_report)
        return
    av = ak.to_numpy(a)
    bv = ak.to_numpy(b)
    bad, n_in, mabs, mrel = compare_arrays(av, bv, st.tol)
    st.inexact += n_in
    if n_in:
        st.max_abs = max(st.max_abs, mabs)
        st.max_rel = max(st.max_rel, mrel)
    if bad.any():
        st.bad_entries += int(np.unique(entry_ref[bad]).size)
        for i in np.flatnonzero(bad):
            if len(st.first) >= max_report:
                break
            st.first.append({"entry": int(entry_ref[i]), "entry_new": int(entry_new[i]), "key": keyfn(i),
                             "ref": _py(av[i]), "new": _py(bv[i]),
                             "diff": _py(float(av[i]) - float(bv[i])) if av.dtype != np.bool_ else None})


def _read(o, fields, start, stop):
    return o.arrays(fields, entry_start=start, entry_stop=stop)


def _key_arrays(o, key):
    arr = o.arrays(key)
    return [ak.to_numpy(arr[k]) for k in key]


def _match_keys(kr, kn, tbr=(), tbn=()):
    """Match entries on the key columns. Entries sharing a key are matched by their rank in the
    tie-break columns tbr / tbn (scalar fields, sorted ascending; file order if none).
    Returns (ref_idx, new_idx, only_ref, only_new, n_dup)."""
    nr = len(kr[0])
    cols = [np.concatenate([np.asarray(a).astype(np.int64, copy=False) if a.dtype != np.uint64
                            else a.view(np.int64), np.asarray(b).astype(np.int64, copy=False)
                            if b.dtype != np.uint64 else b.view(np.int64)]) for a, b in zip(kr, kn)]
    stacked = np.stack(cols, axis=1)
    _, inv = np.unique(stacked, axis=0, return_inverse=True)
    inv = inv.ravel()
    del stacked, cols
    ids_r, ids_n = inv[:nr], inv[nr:]

    def ranks(ids, tbs):
        order = np.lexsort(tuple(reversed(tbs)) + (ids,)) if tbs else np.argsort(ids, kind="stable")
        s = ids[order]
        start = np.r_[0, np.flatnonzero(np.diff(s)) + 1]
        first = np.repeat(start, np.diff(np.r_[start, s.size]))
        r = np.empty_like(ids)
        r[order] = np.arange(s.size) - first
        return r

    rr, rn = ranks(ids_r, list(tbr)), ranks(ids_n, list(tbn))
    n_dup = int((rr > 0).sum() + (rn > 0).sum())
    mult = int(max(rr.max(initial=0), rn.max(initial=0))) + 1
    cr = ids_r.astype(np.int64) * mult + rr
    cn = ids_n.astype(np.int64) * mult + rn
    _, ir, in_ = np.intersect1d(cr, cn, assume_unique=True, return_indices=True)
    order = np.argsort(ir)
    ir, in_ = ir[order], in_[order]
    only_r = np.setdiff1d(np.arange(nr), ir)
    only_n = np.setdiff1d(np.arange(len(kn[0])), in_)
    return ir, in_, only_r, only_n, n_dup


def compare_rntuple(path, orr, onn, rules, key, chunk_size, max_report, tiebreak="auto"):
    res = {"type": "rntuple", "status": "identical", "issues": [], "fields": [], "warnings": []}
    issues = res["issues"]
    fr, fn = rntuple_fields(orr), rntuple_fields(onn)
    res["entries_ref"], res["entries_new"] = int(orr.num_entries), int(onn.num_entries)
    try:
        res["storage_ref"], res["storage_new"] = rntuple_storage(orr), rntuple_storage(onn)
    except Exception as exc:  # storage is information only
        res["warnings"].append({"what": "storage", "error": repr(exc)})
    for name in fr:
        if name not in fn and not rules.for_name(f"{path}:{name}").ignore:
            issues.append({"what": "field only in REF", "field": name, "type": fr[name]})
    for name in fn:
        if name not in fr and not rules.for_name(f"{path}:{name}").ignore:
            issues.append({"what": "field only in NEW", "field": name, "type": fn[name]})
    common = [n for n in fr if n in fn and not rules.for_name(f"{path}:{n}").ignore]
    for name in common:
        if fr[name] != fn[name]:
            issues.append({"what": "field type", "field": name, "ref": fr[name], "new": fn[name]})
    if res["entries_ref"] != res["entries_new"]:
        issues.append({"what": "entries", "ref": res["entries_ref"], "new": res["entries_new"]})

    key = [k for k in key if k in fr and k in fn]
    nr, nn = res["entries_ref"], res["entries_new"]
    mode = "order"
    if key:
        kr, kn = _key_arrays(orr, key), _key_arrays(onn, key)
        same_order = nr == nn and all(np.array_equal(a, b) for a, b in zip(kr, kn))
        if not same_order:
            mode = "key"
    elif nr != nn:
        res["warnings"].append({"what": "no event key in both RNTuples: compared the first "
                                        f"{min(nr, nn)} entries in order"})
    res["mode"] = mode
    stats = {}

    def tol_of(name):
        t = fr[name]
        integer = not ("float" in t or "double" in t or "Float16" in t)
        return rules.for_name(f"{path}:{name}", integer=integer)

    for name in common:
        stats[name] = FieldStats(name, tol_of(name))

    if not common:
        pass
    elif mode == "order":
        n = min(nr, nn)
        if key:
            def keyfn_factory(offset):
                return lambda i: [int(kr[j][offset + i]) for j in range(len(key))]
        else:
            def keyfn_factory(offset):
                return lambda i: None
        for start in range(0, n, chunk_size):
            stop = min(n, start + chunk_size)
            ar = _read(orr, common, start, stop)
            an = _read(onn, common, start, stop)
            ent = np.arange(start, stop)
            kf = keyfn_factory(start)
            for name in common:
                compare_values(ar[name], an[name], ent, ent, kf, stats[name], max_report)
            del ar, an
    else:
        tb = []
        if tiebreak == "auto":
            tb = [n for n in common if n not in key and fr[n] in ("float", "double")][:3]
        elif tiebreak and tiebreak != "none":
            tb = [n for n in tiebreak.split(",") if n in common]
        tbr = [ak.to_numpy(orr.arrays([n])[n]) for n in tb]
        tbn = [ak.to_numpy(onn.arrays([n])[n]) for n in tb]
        ir, in_, only_r, only_n, n_dup = _match_keys(kr, kn, tbr, tbn)
        del tbr, tbn
        res["matched"] = int(ir.size)
        res["key"] = key
        if n_dup:
            res["warnings"].append({"what": f"{n_dup} entries (REF + NEW) repeat a key ({', '.join(key)}) "
                                            "of an earlier entry: matched within the key by the rank in "
                                            + (", ".join(tb) if tb else "file order")})
        if nr == nn and ir.size == nr:
            res["warnings"].append({"what": "entry order differs (all keys matched)"})
        for side, idx, kk in (("REF", only_r, kr), ("NEW", only_n, kn)):
            if idx.size:
                issues.append({"what": f"keys only in {side}", "n": int(idx.size),
                               "first": [[int(kk[j][i]) for j in range(len(key))] for i in idx[:max_report]]})

        def keyfn_m(i):
            return [int(kr[j][ir[i]]) for j in range(len(key))]

        for name in common:
            ar = orr.arrays([name])[name]
            an = onn.arrays([name])[name]
            for start in range(0, ir.size, chunk_size):
                sl = slice(start, start + chunk_size)
                compare_values(ar[ir[sl]], an[in_[sl]], ir[sl], in_[sl],
                               (lambda i, _s=start: keyfn_m(_s + i)), stats[name], max_report)
            del ar, an

    inexact = False
    for name in common:
        st = stats[name]
        if st.bad_entries:
            res["fields"].append(st.as_dict())
        elif st.inexact:
            inexact = True
            d = st.as_dict()
            d["within_tolerance"] = True
            res["fields"].append(d)
    if issues or any(s.bad_entries for s in stats.values()):
        res["status"] = "different"
    elif inexact:
        res["status"] = "within_tolerance"
    return res


# ----------------------------------------------------------------------------------------------
def compare_files(ref, new, tol_rel=0.0, tol_abs=0.0, allow=None, key=("run", "lumi", "event"),
                  chunk_size=200000, max_report=5, only=None, skip=None, log=None, tiebreak="auto"):
    """Compare two files; returns the result dict (see the module docstring)."""
    t0 = time.time()
    rules = Rules(allow, tol_abs, tol_rel)
    out = {"ref": ref, "new": new, "objects": {}, "summary": {}, "only_ref": [], "only_new": [],
           "class_mismatch": [], "dirs_only_ref": [], "dirs_only_new": []}
    fr = uproot.open(ref)
    fn = uproot.open(new)
    try:
        objr, dirr = list_objects(fr)
        objn, dirn = list_objects(fn)
        out["dirs_only_ref"] = sorted(d for d in dirr - dirn if selected(d, only, skip)
                                      and not rules.for_name(d).ignore)
        out["dirs_only_new"] = sorted(d for d in dirn - dirr if selected(d, only, skip)
                                      and not rules.for_name(d).ignore)
        for p in sorted(objr):
            if p not in objn and selected(p, only, skip) and not rules.for_name(p).ignore:
                out["only_ref"].append(p)
        for p in sorted(objn):
            if p not in objr and selected(p, only, skip) and not rules.for_name(p).ignore:
                out["only_new"].append(p)
        counts = {}
        for p in sorted(objr):
            if p not in objn or not selected(p, only, skip):
                continue
            tol = rules.for_name(p)
            if tol.ignore:
                counts["ignored"] = counts.get("ignored", 0) + 1
                continue
            cls_r, cls_n = objr[p], objn[p]
            if cls_r != cls_n:
                out["class_mismatch"].append({"path": p, "ref": cls_r, "new": cls_n})
                continue
            try:
                if cls_r.startswith(HIST_PREFIXES):
                    r = compare_hist(p, fr[p], fn[p], tol, max_report)
                elif "RNTuple" in cls_r:
                    if log:
                        log(f"  rntuple {p} ...")
                    r = compare_rntuple(p, fr[p], fn[p], rules, list(key), chunk_size, max_report, tiebreak)
                else:
                    r = compare_other(p, fr[p], fn[p])
            except Exception as exc:
                r = {"type": "error", "status": "different", "issues": [{"what": "read error",
                                                                         "error": repr(exc)}]}
            r["class"] = cls_r
            out["objects"][p] = r
            kind = r["type"]
            c = counts.setdefault(kind, {"compared": 0, "identical": 0, "within_tolerance": 0,
                                         "different": 0})
            c["compared"] += 1
            c[r["status"]] += 1
        out["summary"] = counts
    finally:
        fr.close()
        fn.close()
    n_diff = sum(c["different"] for k, c in out["summary"].items() if isinstance(c, dict))
    out["n_different"] = n_diff + len(out["only_ref"]) + len(out["only_new"]) + len(out["class_mismatch"]) \
        + len(out["dirs_only_ref"]) + len(out["dirs_only_new"])
    out["identical"] = out["n_different"] == 0
    out["seconds"] = round(time.time() - t0, 2)
    return out


# ----------------------------------------------------------------------------------------------
def _fmt_bytes(n):
    return f"{n / 1e6:9.2f}"


def print_report(res, quiet=False, max_report=5, stream=sys.stdout):
    w = stream.write
    w(f"REF: {res['ref']}\nNEW: {res['new']}\n")
    for label, items in (("objects only in REF", res["only_ref"]), ("objects only in NEW", res["only_new"]),
                         ("directories only in REF", res["dirs_only_ref"]),
                         ("directories only in NEW", res["dirs_only_new"])):
        if items:
            w(f"[DIFF] {len(items)} {label}: {', '.join(items[:max_report])}"
              f"{' ...' if len(items) > max_report else ''}\n")
    for cm in res["class_mismatch"]:
        w(f"[DIFF] class of {cm['path']}: REF {cm['ref']}, NEW {cm['new']}\n")
    for path, r in res["objects"].items():
        st = r["status"]
        if st == "identical" and not r.get("warnings"):
            continue
        if st == "identical" and quiet:
            continue
        tag = {"different": "[DIFF]", "within_tolerance": "[TOL ]", "identical": "[WARN]"}[st]
        if r["type"] == "histogram":
            if st == "different" or not quiet:
                w(f"{tag} {r['class']} {path} (tolerance {r.get('tolerance')})")
                if "integral_ref" in r:
                    w(f": integral REF {r['integral_ref']:.10g} NEW {r['integral_new']:.10g}")
                w("\n")
            for it in r["issues"]:
                if "n_bins" in it:
                    w(f"       {it['what']}: {it['n_bins']} / {it['n_cells']} bins differ, max abs "
                      f"{it['max_abs']:.3g}, max rel {it['max_rel']:.3g}\n")
                    for fb in it["first"]:
                        w(f"         {fb['bin']}: REF {fb['ref']!r} NEW {fb['new']!r}\n")
                else:
                    w(f"       {it['what']}: REF {it.get('ref')!r} NEW {it.get('new')!r}\n")
            if not quiet:
                for it in r.get("within_tolerance", []):
                    w(f"       {it['what']}: {it['n_bins']} bins not exact, within tolerance (max abs "
                      f"{it['max_abs']:.3g}, max rel {it['max_rel']:.3g})\n")
                for it in r.get("warnings", []):
                    w(f"       warning {it['what']}: REF {it.get('ref')!r} NEW {it.get('new')!r}\n")
        elif r["type"] == "rntuple":
            w(f"{tag} RNTuple {path}: entries REF {r['entries_ref']} NEW {r['entries_new']}, mode {r.get('mode')}"
              + (f", matched {r['matched']}" if "matched" in r else "") + "\n")
            for it in r["issues"]:
                w(f"       {it['what']}: " + ", ".join(f"{k} {v}" for k, v in it.items() if k != "what") + "\n")
            for it in r.get("warnings", []):
                w(f"       warning: {it['what']}\n")
            for fs in r["fields"]:
                if fs.get("within_tolerance") and quiet:
                    continue
                w(f"       field {fs['field']} ({fs['tolerance']}): "
                  + ("within tolerance, " if fs.get("within_tolerance") else
                     f"{fs['entries_beyond_tol']} entries differ, ")
                  + f"{fs['values_not_exact']} values not exact, max abs {fs['max_abs']:.3g}, max rel "
                    f"{fs['max_rel']:.3g}" + (f", {fs['length_mismatch']} length mismatches"
                                             if fs["length_mismatch"] else "") + "\n")
                if not fs.get("within_tolerance"):
                    for e in fs["first"]:
                        w(f"         entry {e['entry']}" + (f" (NEW {e['entry_new']})" if e['entry_new'] != e['entry'] else "")
                          + (f" key {e['key']}" if e.get("key") else "")
                          + (f" {e['what']}" if e.get("what") else "")
                          + f": REF {e['ref']!r} NEW {e['new']!r}\n")
        else:
            w(f"{tag} {r.get('class')} {path}\n")
            for it in r["issues"]:
                w(f"       {it}\n")
    # storage table
    rows = [(p, r) for p, r in res["objects"].items() if r["type"] == "rntuple" and "storage_ref" in r]
    if rows:
        w("RNTuple storage (MB on disk; compression of the pages; columns whose encoding differs):\n")
        w(f"  {'rntuple':40s} {'entries':>10s} {'REF MB':>9s} {'NEW MB':>9s} {'NEW/REF':>7s} "
          f"{'REF comp':>10s} {'NEW comp':>10s} {'clusters R/N':>12s}\n")
        tot_r = tot_n = 0
        for p, r in rows:
            sr, sn = r["storage_ref"], r["storage_new"]
            tot_r += sr["bytes_on_disk"]
            tot_n += sn["bytes_on_disk"]
            ratio = sn["bytes_on_disk"] / sr["bytes_on_disk"] if sr["bytes_on_disk"] else float("nan")
            w(f"  {p[:40]:40s} {sr['entries']:10d} {_fmt_bytes(sr['bytes_on_disk'])} {_fmt_bytes(sn['bytes_on_disk'])} "
              f"{ratio:7.3f} {','.join(sr['compression_names']):>10s} {','.join(sn['compression_names']):>10s} "
              f"{sr['clusters']:>5d}/{sn['clusters']:<6d}\n")
            encd = [f"{k}: {','.join(sr['encodings'].get(k, []))} -> {','.join(sn['encodings'].get(k, []))}"
                    for k in sorted(set(sr["encodings"]) | set(sn["encodings"]))
                    if sr["encodings"].get(k) != sn["encodings"].get(k)]
            if encd:
                w("      encodings: " + "; ".join(encd) + "\n")
        ratio = tot_n / tot_r if tot_r else float("nan")
        w(f"  {'total':40s} {'':10s} {_fmt_bytes(tot_r)} {_fmt_bytes(tot_n)} {ratio:7.3f}\n")
    w("summary: ")
    parts = []
    for kind, c in res["summary"].items():
        if isinstance(c, dict):
            parts.append(f"{kind} {c['compared']} compared: {c['identical']} identical, "
                         f"{c['within_tolerance']} within tolerance, {c['different']} different")
        else:
            parts.append(f"{c} {kind}")
    w("; ".join(parts) + "\n")
    w(f"RESULT: {'IDENTICAL (within tolerances)' if res['identical'] else 'DIFFERENT'} "
      f"({res['n_different']} differences, {res['seconds']} s)\n")


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, set):
        return sorted(o)
    return str(o)


def _clean_json(o):
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return repr(o)
    if isinstance(o, dict):
        return {k: _clean_json(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean_json(v) for v in o]
    return o


def add_common_args(p):
    p.add_argument("--tol-rel", type=float, default=0.0, help="relative tolerance of all float values (default 0: exact)")
    p.add_argument("--tol-abs", type=float, default=0.0, help="absolute tolerance of all float values (default 0)")
    p.add_argument("--allow", action="append", default=[], metavar="PATTERN=TOL",
                   help="tolerance for matching objects / fields (<rntuple>:<field>); TOL = X | rel:X | abs:X | "
                        "abs:X,rel:Y | ignore; repeatable, first match wins")
    p.add_argument("--key", default="run,lumi,event", help="RNTuple event key fields (default run,lumi,event)")
    p.add_argument("--tiebreak", default="auto",
                   help="key-matched mode: scalar fields that order entries sharing a key (comma list, 'none' = "
                        "file order; default auto = the first three float fields)")
    p.add_argument("--chunk-size", type=int, default=200000, help="RNTuple entries per read (default 200000)")
    p.add_argument("--max-report", type=int, default=5, help="differences listed per object / field (default 5)")
    p.add_argument("--only", action="append", default=[], metavar="GLOB", help="compare only matching objects")
    p.add_argument("--skip", action="append", default=[], metavar="GLOB", help="skip matching objects")
    p.add_argument("--quiet", action="store_true", help="list only the differences beyond tolerance")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ref")
    p.add_argument("new")
    add_common_args(p)
    p.add_argument("--json", help="write the full result as JSON")
    a = p.parse_args(argv)
    try:
        res = compare_files(a.ref, a.new, a.tol_rel, a.tol_abs, a.allow,
                            [k for k in a.key.split(",") if k], a.chunk_size, a.max_report, a.only, a.skip,
                            tiebreak=a.tiebreak)
    except (OSError, ValueError) as exc:
        print(f"compare_outputs.py: error: {exc}", file=sys.stderr)
        return 2
    print_report(res, a.quiet, a.max_report)
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(_clean_json(res), fh, indent=1, default=_json_default)
    return 0 if res["identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
