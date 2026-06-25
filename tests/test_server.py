import sys,os
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

XML='<InsuranceSvcRq><Policy><PolicyNumber>P123</PolicyNumber><PersonName><Surname>Doe</Surname></PersonName></Policy></InsuranceSvcRq>'
def test_parse():
    p=server.parse_acord(XML); assert p.policy_number=="P123"; assert p.has_personal_data
def test_validate():
    assert server.validate_acord(XML).valid
def test_govern():
    assert any("Solvency" in f for f in server.govern_insurance(XML).frameworks)
