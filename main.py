#!/usr/bin/env python3
"""
Sistem Pakar Identifikasi Gangguan Wi-Fi pada Windows
Mesin inferensi Forward Chaining dibuat secara mandiri.
"""
import argparse
import json
from pathlib import Path

def load_knowledge(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    required = {"judul", "batas", "sumber", "pertanyaan", "aturan", "kesimpulan_akhir", "label"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Struktur basis pengetahuan tidak lengkap: {', '.join(sorted(missing))}")
    return data

def rule_is_satisfied(rule, memory):
    conditions = rule["jika"]
    if rule["mode"] == "dan":
        return all(condition in memory for condition in conditions)
    if rule["mode"] == "atau":
        return any(condition in memory for condition in conditions)
    raise ValueError(f"Mode aturan tidak dikenal pada {rule.get('id')}")

def forward_chaining(knowledge, initial_facts):
    """
    Memulai dari fakta awal, memeriksa aturan, menambahkan fakta baru,
    dan mengulang sampai tidak ada aturan baru yang dapat dijalankan.
    """
    memory = set(initial_facts)
    proof = {}
    fired_rules = []
    cycle = 0

    while True:
        new_rule_found = False
        for rule in knowledge["aturan"]:
            conclusion = rule["maka"]
            if conclusion in memory:
                continue
            if rule_is_satisfied(rule, memory):
                cycle += 1
                memory.add(conclusion)
                proof[conclusion] = {
                    "rule": rule,
                    "conditions": list(rule["jika"]),
                    "cycle": cycle
                }
                fired_rules.append(rule)
                print(f"  Siklus {cycle}: {rule['id']} -> {knowledge['label'].get(conclusion, conclusion)}")
                new_rule_found = True
                # Mulai pemeriksaan ulang dari aturan pertama setelah fakta baru masuk.
                break
        if not new_rule_found:
            break

    return memory, proof, fired_rules

def explain_fact(fact, proof, labels, sources, indent=0, visited=None):
    if visited is None:
        visited = set()
    prefix = " " * indent
    label = labels.get(fact, fact)
    if fact not in proof:
        print(f"{prefix}- Fakta awal: {label}")
        return
    if fact in visited:
        print(f"{prefix}- {label} (siklus/rujukan berulang dihindari)")
        return
    visited.add(fact)
    item = proof[fact]
    rule = item["rule"]
    source = sources[rule["sumber"]]
    print(f"{prefix}- {label} <- {rule['id']} [{rule['sumber']}: {source['penerbit']}]")
    for condition in item["conditions"]:
        explain_fact(condition, proof, labels, sources, indent + 4, visited)

def ask_user(knowledge):
    facts = set()
    print("\nJawab pertanyaan berikut dengan y (ya) atau t (tidak).")
    for index, item in enumerate(knowledge["pertanyaan"], start=1):
        while True:
            answer = input(f"{index}. {item['teks']} (y/t): ").strip().lower()
            if answer in {"y", "ya"}:
                facts.add(item["fakta"])
                break
            if answer in {"t", "tidak"}:
                break
            print("Masukkan hanya y atau t.")
    return facts

def run_case(knowledge, initial_facts, case_name="Kasus"):
    labels = knowledge["label"]
    print("\n" + "=" * 68)
    print(knowledge["judul"])
    print(f"Pengujian: {case_name}")
    print("=" * 68)
    print("Fakta awal:")
    if initial_facts:
        for fact in sorted(initial_facts):
            print(f"  - {labels.get(fact, fact)}")
    else:
        print("  - Tidak ada fakta yang dijawab YA.")

    print("\nProses Forward Chaining:")
    memory, proof, fired = forward_chaining(knowledge, initial_facts)

    conclusions = [fact for fact in knowledge["kesimpulan_akhir"] if fact in memory]
    print("\nHasil:")
    if not conclusions:
        print("  Tidak ditemukan kesimpulan berdasarkan aturan yang tersedia.")
    else:
        for conclusion in conclusions:
            print(f"\nKESIMPULAN: {labels.get(conclusion, conclusion)}")
            print("Alasan penelusuran:")
            explain_fact(conclusion, proof, labels, knowledge["sumber"], indent=2)

    if not fired:
        print("\nTidak ada aturan yang terpenuhi.")
    print("\nBatas keberlakuan:")
    print(knowledge["batas"])
    print("=" * 68)
    return conclusions

def main():
    parser = argparse.ArgumentParser(description="Sistem Pakar Gangguan Wi-Fi dengan Forward Chaining")
    parser.add_argument("--kb", default="kb_wifi.json", help="Lokasi file basis pengetahuan JSON")
    parser.add_argument("--demo", choices=["dhcp", "sinyal", "negatif", "dns", "bandwidth", "interferensi"],
                        help="Jalankan skenario uji yang telah disiapkan")
    args = parser.parse_args()

    try:
        knowledge = load_knowledge(args.kb)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Gagal membaca basis pengetahuan: {error}")
        return

    demo_cases = {
        "dhcp": {
            "nama": "Kasus 1 - Dugaan gangguan DHCP",
            "fakta": {"wifi_terhubung", "tidak_ada_internet", "ip_169"}
        },
        "sinyal": {
            "nama": "Kasus 2 - Dugaan gangguan kualitas sinyal",
            "fakta": {"rssi_le_minus_80", "internet_lambat"}
        },
        "negatif": {
            "nama": "Kasus 3 - Kasus negatif (tidak ada kesimpulan)",
            "fakta": {"wifi_terhubung"}
        },
        "dns": {
            "nama": "Kasus tambahan - Dugaan masalah DNS",
            "fakta": {"wifi_terhubung", "tidak_ada_internet", "ip_valid", "akses_ip_berhasil_domain_gagal"}
        },
        "bandwidth": {
            "nama": "Kasus tambahan - Pemakaian bandwidth",
            "fakta": {"aplikasi_bandwidth_aktif", "internet_lambat"}
        },
        "interferensi": {
            "nama": "Kasus tambahan - Interferensi Wi-Fi",
            "fakta": {"interferensi_teridentifikasi", "koneksi_tidak_stabil"}
        }
    }

    if args.demo:
        case = demo_cases[args.demo]
        run_case(knowledge, case["fakta"], case["nama"])
    else:
        print(knowledge["judul"])
        print("Mesin inferensi: Forward Chaining")
        print("Basis pengetahuan dibaca dari:", args.kb)
        facts = ask_user(knowledge)
        run_case(knowledge, facts, "Input pengguna")

if __name__ == "__main__":
    main()
