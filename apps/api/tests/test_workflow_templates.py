from agi_server.workflow.templates import GROWTH_WORKFLOW_TEMPLATES, list_workflow_templates


def test_list_workflow_templates():
    templates = list_workflow_templates()
    assert len(templates) == 4
    ids = [t["id"] for t in templates]
    assert "lead-discovery-enrichment" in ids
    assert "competitive-battlecard" in ids
    assert "inbound-intent-triage" in ids
    assert "crm-erp-data-hygiene" in ids


def test_template_structure_validation():
    for tpl in GROWTH_WORKFLOW_TEMPLATES:
        assert "id" in tpl
        assert "name" in tpl
        assert "nodes" in tpl
        assert "edges" in tpl
        assert len(tpl["nodes"]) >= 2
        assert len(tpl["edges"]) >= 1
