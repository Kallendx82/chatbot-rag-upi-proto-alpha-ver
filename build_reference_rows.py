"""build_reference_rows.py  (run with SYSTEM python — needs pandas)
=============================================================================
Stage 1 of adding reference chunks: build the chunk dicts (NO embedding) and
write them to reference_rows.json. Stage 2 (embed_reference_rows.py, run with
the backend VENV python which has CPU-only torch) embeds + appends them.

Produces high-signal reference chunks for common list questions:
  - Program studi per fakultas/kampus (from the official 2026 UKT Master sheet).
  - Jenis beasiswa di UPI (general + per-year, grounded in Laporan Tahunan UPI).
  - Daftar fakultas + kampus (kept here as the single source of truth).
=============================================================================
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Project\RAG_UPI")
PMB = ROOT / "Dataset" / "PMB UPI" / "Biaya Pendidikan UPI Tahun Akademik 2025-2026"
MASTER = (PMB / "KEPUTUSAN REKTOR UNIVERSITAS PENDIDIKAN INDONESIA NOMOR 4-UN40-KU.00.00-2026"
              / "Lampiran NOMOR 4-UN40-KU.00.00-2026.xlsx")
PEDOMAN = str(ROOT / "Dataset" / "Pedoman-Penyelenggaran-Pendidikan-UPI-Tahun-2024-rev.pdf")
LAPORAN = str(ROOT / "Dataset" / "PPID")
OUT = ROOT / "reference_rows.json"


def _clean(s) -> str:
    return " ".join(str(s).split()).strip()


def _row(rid, title, source, text, keywords, category="Referensi UPI"):
    return {
        "doc_id": rid, "source": source, "url": None, "title": title,
        "category": category, "source_type": "pdf", "page": 1,
        "section": "Referensi ringkas", "text": text,
        "chunk_length": len(text), "chunk_index": 0,
        "chunk_id": f"{rid}::0", "keywords": keywords,
    }


def prodi_per_fakultas() -> list[dict]:
    """One chunk per Fakultas/Kampus listing its S1 study programs (2026 UKT Master)."""
    df = pd.read_excel(MASTER, sheet_name="Master", header=0, dtype=str)
    c = list(df.columns)
    groups: dict[str, list[str]] = {}
    order: list[str] = []
    for _, r in df.iterrows():
        fak = _clean(r[c[1]]); prodi = _clean(r[c[3]]); jenjang = _clean(r[c[2]])
        if not fak or not prodi or prodi.lower() == "nan":
            continue
        if fak not in groups:
            groups[fak] = []; order.append(fak)
        label = f"{jenjang} {prodi}".strip()
        if label not in groups[fak]:
            groups[fak].append(label)
    rows = []
    for i, fak in enumerate(order):
        prodi_list = "; ".join(groups[fak])
        title_fak = fak.title() if fak.isupper() else fak
        text = (
            f"Daftar program studi (jurusan) di {title_fak}, Universitas "
            f"Pendidikan Indonesia (UPI). Program studi yang ada di {title_fak} "
            f"antara lain: {prodi_list}. (Sumber: Keputusan Rektor UPI Tahun "
            f"2026 tentang UKT / daftar program studi UPI.)"
        )
        rid = f"ref_prodi_{i:02d}"
        rows.append(_row(rid, f"Program Studi — {title_fak}", str(MASTER), text,
                         ["program studi", "prodi", "jurusan", title_fak.lower()]))
    return rows


def fakultas_dan_kampus() -> list[dict]:
    fak_text = (
        "Daftar fakultas di Universitas Pendidikan Indonesia (UPI). Berdasarkan "
        "Pedoman Penyelenggaraan Pendidikan UPI Tahun 2024, UPI memiliki 9 "
        "(sembilan) fakultas, Sekolah Pascasarjana, dan 5 kampus daerah. "
        "Fakultas/jurusan di UPI yaitu: 1. Fakultas Ilmu Pendidikan (FIP); "
        "2. Fakultas Pendidikan Ilmu Pengetahuan Sosial (FPIPS); 3. Fakultas "
        "Pendidikan Bahasa dan Sastra (FPBS); 4. Fakultas Pendidikan Matematika "
        "dan Ilmu Pengetahuan Alam (FPMIPA); 5. Fakultas Pendidikan Teknologi "
        "dan Kejuruan (FPTK); 6. Fakultas Pendidikan Olahraga dan Kesehatan "
        "(FPOK); 7. Fakultas Pendidikan Ekonomi dan Bisnis (FPEB); 8. Fakultas "
        "Pendidikan Seni dan Desain (FPSD); 9. Fakultas Kedokteran (FK). Selain "
        "itu terdapat Sekolah Pascasarjana (SPs) serta 5 Kampus UPI di Daerah: "
        "Kampus Cibiru, Kampus Sumedang, Kampus Tasikmalaya, Kampus Purwakarta, "
        "dan Kampus Serang."
    )
    kampus_text = (
        "Lokasi kampus Universitas Pendidikan Indonesia (UPI). Kampus utama UPI "
        "adalah Kampus Bumi Siliwangi di Kota Bandung. Selain itu, UPI memiliki "
        "5 (lima) kampus daerah, yaitu: Kampus UPI di Cibiru (Bandung), Kampus "
        "UPI di Sumedang, Kampus UPI di Tasikmalaya, Kampus UPI di Purwakarta, "
        "dan Kampus UPI di Serang. UPI juga menyelenggarakan Sekolah "
        "Pascasarjana (SPs) untuk program magister dan doktor."
    )
    return [
        _row("ref_fakultas_upi", "Daftar Fakultas di UPI", PEDOMAN, fak_text,
             ["fakultas", "daftar fakultas", "fip", "fpmipa", "upi"]),
        _row("ref_kampus_upi", "Kampus UPI di Daerah", PEDOMAN, kampus_text,
             ["kampus", "kampus daerah", "cibiru", "sumedang", "serang", "upi"]),
    ]


def beasiswa() -> list[dict]:
    umum = (
        "Jenis-jenis beasiswa di Universitas Pendidikan Indonesia (UPI). UPI "
        "menyalurkan beragam beasiswa bagi mahasiswa, baik dari pemerintah, "
        "pemerintah daerah, perusahaan, bank, maupun yayasan. Jenis beasiswa "
        "yang umum tersedia antara lain: KIP-Kuliah (sebelumnya Bidikmisi); "
        "Beasiswa Peningkatan Prestasi Akademik (PPA); Beasiswa Unggulan "
        "Kemendikbudristek; Beasiswa Pendidikan Indonesia (BPI) untuk S1, S2, "
        "dan S3; Beasiswa Bank Indonesia; Beasiswa Cendekia BAZNAS; Beasiswa "
        "Karya Salemba Empat (KSE); Beasiswa Djarum; Beasiswa dari Pemerintah "
        "Provinsi Jawa Barat (JFL/JFLS); Beasiswa Afirmasi/ADik untuk mahasiswa "
        "difabel; serta beasiswa dari berbagai bank dan perusahaan (BRI, BNI, "
        "dll). Pengelolaan beasiswa dilakukan oleh Direktorat Kemahasiswaan UPI "
        "(dan Sekolah Pascasarjana untuk jenjang pascasarjana). Jenis beasiswa "
        "yang tersedia dapat berbeda tiap tahun. (Sumber: Laporan Tahunan UPI.)"
    )
    b2022 = (
        "Beasiswa di UPI pada tahun 2022. Menurut Laporan Tahunan UPI 2022, "
        "terdapat sekitar 15 jenis beasiswa dari 13 lembaga pemberi beasiswa "
        "dengan total 7.935 mahasiswa penerima. Jenis beasiswa tahun 2022 "
        "antara lain: KIP-Kuliah (KIPK), Beasiswa Karya Salemba Empat (KSE), "
        "Beasiswa Pancakarsa Kabupaten Bogor, Beasiswa SMART BRILIAN (Lembaga "
        "Amil Zakat BRI), Beasiswa BRI, Beasiswa Bank Indonesia, Beasiswa "
        "Cendekia BAZNAS, Beasiswa Unggulan Kemendikbudristek, Beasiswa "
        "Pendidikan Indonesia (S1/S2/S3), Beasiswa Djarum, Beasiswa JFL/JFLS "
        "Pemerintah Provinsi Jawa Barat, Beasiswa ADik untuk difabel, Beasiswa "
        "RMP Pemerintah Kota Bandung, serta beasiswa dari beberapa yayasan. "
        "(Sumber: Laporan Tahunan UPI 2022.)"
    )
    b2017 = (
        "Beasiswa di UPI pada tahun 2017. Menurut Laporan Tahunan UPI 2017, "
        "jenis beasiswa yang disalurkan kepada mahasiswa antara lain: Bidikmisi, "
        "Beasiswa Afirmasi, Beasiswa Peningkatan Prestasi Akademik (PPA) "
        "termasuk kuota tambahan, Beasiswa Pemerintah Provinsi Jawa Barat, "
        "Beasiswa Kabupaten Bandung Barat (KBB), Beasiswa Bank Indonesia (BI), "
        "Bawaku Prestasi, Bawaku SKTM, dan Beasiswa BNI. (Sumber: Laporan "
        "Tahunan UPI 2017.)"
    )
    src = LAPORAN
    return [
        _row("ref_beasiswa_umum", "Jenis Beasiswa di UPI", src, umum,
             ["beasiswa", "jenis beasiswa", "kip kuliah", "ppa", "bidikmisi"]),
        _row("ref_beasiswa_2022", "Beasiswa UPI Tahun 2022", src, b2022,
             ["beasiswa", "beasiswa 2022", "kipk", "upi"]),
        _row("ref_beasiswa_2017", "Beasiswa UPI Tahun 2017", src, b2017,
             ["beasiswa", "beasiswa 2017", "bidikmisi", "ppa"]),
    ]


def main() -> None:
    rows = fakultas_dan_kampus() + prodi_per_fakultas() + beasiswa()
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[build] wrote {len(rows)} reference rows -> {OUT}")
    for r in rows:
        print(f"   - {r['chunk_id']:<22} {r['title']}")


if __name__ == "__main__":
    main()
