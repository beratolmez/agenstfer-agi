from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import Any

from agi_server.schemas import DemoCounts

DEMO_COMPANY = "Anka Endüstriyel Otomasyon"
SEED = 20260713


def build_demo_dataset() -> dict[str, list[dict[str, Any]]]:
    """Create a deterministic industrial B2B dataset through the adapter-facing shape."""
    rng = random.Random(SEED)
    sectors = ["Otomotiv", "Gıda", "Kimya", "Makine", "Metal", "Ambalaj"]
    cities = ["Bursa", "Kocaeli", "İstanbul", "İzmir", "Konya", "Ankara"]
    key_account_names = [
        "Arçelik A.Ş.",
        "Tofaş Türk Otomobil Fabrikası",
        "Ford Otosan",
        "Vestel Elektronik",
        "GlobalBank",
        "Acme Corp",
        "StartUpXYZ",
    ]
    accounts = []
    for index in range(150):
        name = (
            key_account_names[index]
            if index < len(key_account_names)
            else f"{sectors[index % len(sectors)]} Sanayi {index + 1:03d}"
        )
        accounts.append(
            {
                "id": f"acc-{index + 1:03d}",
                "name": name,
                "sector": sectors[index % len(sectors)],
                "city": cities[index % len(cities)],
                "annual_revenue_try": rng.randrange(25, 800) * 1_000_000,
                "energy_intensity": round(rng.uniform(0.3, 1.0), 2),
                "installed_base": rng.randrange(1, 18),
                "export_ratio": round(rng.uniform(0, 0.85), 2),
                "lifecycle_status": "active" if index % 17 else "stale",
            }
        )

    contacts = [
        {
            "id": f"con-{index + 1:03d}",
            "account_id": accounts[index % 150]["id"],
            "role": ["Bakım Müdürü", "Fabrika Müdürü", "Satın Alma", "CFO"][index % 4],
            "email": None if index % 29 == 0 else f"contact{index + 1}@example.invalid",
        }
        for index in range(250)
    ]
    opportunities = [
        {
            "id": f"opp-{index + 1:03d}",
            "account_id": accounts[index % 150]["id"],
            "stage": ["Keşif", "Teklif", "Müzakere", "Beklemede"][index % 4],
            "value_try": rng.randrange(200, 5000) * 1_000,
            "probability": [20, 40, 60, 75][index % 4],
        }
        for index in range(70)
    ]
    products = [
        {
            "id": f"prd-{index + 1:02d}",
            "name": [
                "Anka-PLC-5000 Modular Automation Controller",
                "AnkaDrive-X High-Precision Servo Drive",
                "AnkaTouch-10 IP66 Industrial HMI",
                "AnkaSCADA v4.2 Enterprise Server License",
                "AnkaSense Vibration & Thermal IoT Sensor Node",
                "24/7 Priority Field Service & Maintenance SLA",
                "Robotic Palletizing & Assembly Cell Kit",
                "Energy Retrofit Power Quality & Metering Kit",
                "PLC Modernization & Conversion Kit",
                "OEM Export Compliance Cabinet Kit",
                "Digital Twin 3D Visual Commissioning",
                "Automation Training & Engineering Package",
            ][index],
        }
        for index in range(12)
    ]
    orders_invoices = [
        {
            "id": f"txn-{index + 1:03d}",
            "account_id": accounts[index % 150]["id"],
            "product_id": products[index % 12]["id"],
            "amount_try": rng.randrange(30, 900) * 1_000,
            "kind": "invoice" if index % 2 else "order",
            "date": (datetime(2026, 7, 1, tzinfo=UTC) - timedelta(days=index % 720))
            .date()
            .isoformat(),
        }
        for index in range(400)
    ]
    activities = [
        {
            "id": f"act-{index + 1:04d}",
            "account_id": accounts[index % 150]["id"],
            "kind": ["meeting", "email", "call", "proposal"][index % 4],
            "date": (datetime(2026, 7, 1, tzinfo=UTC) - timedelta(days=index % 365))
            .date()
            .isoformat(),
        }
        for index in range(900)
    ]
    return {
        "accounts": accounts,
        "contacts": contacts,
        "opportunities": opportunities,
        "products": products,
        "orders_invoices": orders_invoices,
        "activities": activities,
    }


def demo_counts(dataset: dict[str, list[dict[str, Any]]]) -> DemoCounts:
    return DemoCounts(**{name: len(rows) for name, rows in dataset.items()})
