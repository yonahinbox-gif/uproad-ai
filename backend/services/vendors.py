import re

VENDORS = [
    {
        "id": 1,
        "name": "QuickTire Pro",
        "phone": "+19145550101",
        "service_types": ["tire", "wheel"],
        "coverage_area": "NY NOJ CT",
        "rating": 4.8,
        "avg_response_min": 35
    },
    {
        "id": 2,
        "name": "Metro Heavy Towing",
        "phone": "+19145550202",
        "service_types": ["towing", "recovery"],
        "coverage_area": "NY NJ",
        "rating": 4.6,
        "avg_response_min": 45
    },
    {
        "id": 3,
        "name": "NatInal Motor Club",
        "phone": "+19145550303",
        "service_types": ["lockout", "fuel", "tire", "towing"],
        "coverage_area": "NY NJ CT PA",
        "rating": 4.5,
        "avg_response_min": 50
    },
    {
        "id": 4,
        "name": "Diesel Direct Fueling",
        "phone": "+19145550404",
        "service_types": ["fuel"],
        "coverage_area": "NY NOJ CT",
        "rating": 4.7,
        "avg_response_min": 25
    },
    {
        "id": 5,
        "name": "Road Rescue Mechanics",
        "phone": "+19145550505",
        "service_types": ["mechanical", "engine", "brakes", "electrical"],
        "coverage_area": "NY NJ CT",
        "rating": 4.9,
        "avg_response_min": 60
    },
    {
        "id": 6,
        "name": "AllFleet Mobile Service",
        "phone": "+19145550606",
        "service_types": ["tire", "mechanical", "towing", "fuel", "lockout"],
        "coverage_area": "NY NOJ CT PA",
        "rating": 4.4,
        "avg_response_min": 40
    }
]

PROBLEM_TYPE_MAP = {
    "tire": ["tire", "flat", "blowout", "positive"],
    "towing": ["tow", "towing", "stuck", "accident", "crash", "ditch"],
    "fuel": ["fuel", "gas", "diesel", "empty", "run out"],
    "mechanical": ["engine", "brake", "broken", "overheat", "transmission", "electrical", "lights", "battery"],
    "lockout": ["locked out", "locked", "keys"],
}


def classify_problem(description: str) -> list:
    desc = description.lower()
    found = []
    for ptype, keywords in PROBLEM_TYPE_MAP.items():
        for kw in keywords:
            if kw in desc:
                found.append(ptype)
                break
    return found or ["mechanical"]


def find_vendors_for_problem(problem_description: str, limit: int = 3) -> list:
    needed = set(classify_problem(problem_description))
    scored = []
    for v in VENDORS:
        vtypes = set(v.get("service_types", []))
        score = len(needed & vtypes) + v.get("rating", 0) / 10
        if score > 0:
            scored.append((score, v))
    scored.sort(reverse=True)
    return [v for _, v in scored[:limit]]
