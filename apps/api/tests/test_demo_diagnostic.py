from agi_server.domain.demo import build_demo_dataset, demo_counts
from agi_server.domain.diagnostic import build_growth_diagnostic


def test_demo_dataset_has_planned_counts_and_is_deterministic():
    first = build_demo_dataset()
    second = build_demo_dataset()
    assert first == second
    assert demo_counts(first).model_dump() == {
        "accounts": 150,
        "contacts": 250,
        "opportunities": 70,
        "products": 12,
        "orders_invoices": 400,
        "activities": 900,
    }


def test_diagnostic_detects_all_planted_signals_with_resolvable_evidence():
    diagnostic = build_growth_diagnostic()
    assert len(diagnostic.detected_planted_insights) >= 5
    assert len(diagnostic.opportunities) == 5
    assert all(item.evidence for item in diagnostic.opportunities)
    assert all(evidence.locator for item in diagnostic.opportunities for evidence in item.evidence)
    assert diagnostic.opportunities == sorted(
        diagnostic.opportunities, key=lambda item: item.score, reverse=True
    )


def test_score_is_deterministic_not_a_probability():
    diagnostic = build_growth_diagnostic()
    assert all(item.score == item.factors.total() for item in diagnostic.opportunities)
    assert "olasılık" in diagnostic.disclaimer


def test_diagnostic_uses_installation_state_company_name_and_objective():
    from agi_server.db import InstallationState
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from agi_server.db import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        inst = InstallationState(
            id="default",
            configuration={"company_name": "Test AŞ", "objective": "Yıllık %30 Büyüme"},
        )
        db.add(inst)
        db.commit()

        diagnostic = build_growth_diagnostic(db)
        assert diagnostic.company == "Test AŞ"
        assert diagnostic.objective == "Yıllık %30 Büyüme"
    engine.dispose()
