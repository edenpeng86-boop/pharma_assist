from src.domain.citation_validator import validate_citations
from src.domain.risk import classify_risk
from src.core.models import Evidence


def test_risk_classifier_marks_high_risk_release():
    assert classify_risk("产品放行前发现重大偏差怎么办？") == "high"


def test_citation_validator_accepts_valid_reference():
    evidence = [Evidence(id="a", source="demo.txt", content="content")]
    check = validate_citations("这是回答。[1]", evidence)
    assert check.grounded is True
