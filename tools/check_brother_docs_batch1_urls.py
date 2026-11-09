TARGETS = {
    108: {
        "model": "BE-438DP",
        "documents": [
            ("Catalog", "BE-438DP Catalog"),
        ],
    },
    111: {
        "model": "KE-430DP",
        "documents": [
            ("Manual", "KE-430DP Instruction Manual"),
            ("Parts List", "KE-430DP Parts Book"),
        ],
    },
    113: {
        "model": "BAS-311HX",
        "documents": [
            ("Manual", "BAS-311HX/BAS-326H Instruction Manual"),
            ("Parts List", "BAS-311HX/BAS-326H Parts Book"),
        ],
    },
    114: {
        "model": "BAS-326HX",
        "documents": [
            ("Manual", "BAS-311HX/BAS-326H Instruction Manual"),
            ("Parts List", "BAS-311HX/BAS-326H Parts Book"),
        ],
    },
}

print("=== BROTHER DOCUMENT DRAFT CHECK ===")
print("MODE: READ ONLY")
print("DATABASE: TIDAK DIUBAH\n")

total = 0

for machine_id, data in TARGETS.items():
    print(f"{machine_id} | {data['model']}")

    for doc_type, title in data["documents"]:
        print(f"  {doc_type:<10} | {title}")
        total += 1

    print()

print(f"TOTAL DRAFT DOCUMENT: {total}")
print("\nSOURCE CHECK:")
print("108 BE-438DP  : Catalog resmi Brother")
print("111 KE-430DP  : Instruction Manual + Parts Book resmi Brother")
print("113 BAS-311HX : Instruction Manual + Parts Book resmi Brother")
print("114 BAS-326HX : Instruction Manual + Parts Book resmi Brother")
print("\nSTATUS: DRAFT SAJA — BELUM ADA INSERT")
