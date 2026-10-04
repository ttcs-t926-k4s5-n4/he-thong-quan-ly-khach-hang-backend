"""
tests/test_custom_fields.py — Automated Integration Tests for SCRUM-66:
- Custom Field Definitions CRUD & Form Schema
- Custom Field Validation (Required, Types: text, number, date, select)
- Customer & Opportunity Integration with Custom Fields
- Dynamic Filter Engine & Excel Export (.xlsx)
"""
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def login_as(client, email="admin@company.vn", password="Admin@123"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp


class TestCustomFieldsAPI:
    def test_create_custom_field_admin_only(self, client):
        # Unauthenticated request should fail
        res = client.post("/api/custom-fields", json={"field_label": "Test"})
        assert res.status_code == 401

        # Login as employee (non-admin)
        login_as(client, "employee@company.vn", "Employee@123")
        res = client.post(
            "/api/custom-fields",
            json={
                "entity_type": "customer",
                "field_key": "test_emp",
                "field_label": "Test Emp",
                "field_type": "text",
            },
        )
        assert res.status_code == 403

        # Login as Admin
        client.post("/api/auth/logout")
        login_as(client, "admin@company.vn", "Admin@123")
        res = client.post(
            "/api/custom-fields",
            json={
                "entity_type": "customer",
                "field_key": "facebook_page",
                "field_label": "Trang Facebook",
                "field_type": "text",
                "is_required": False,
                "description": "Link trang facebook cua doanh nghiep",
            },
        )
        assert res.status_code in (201, 400)  # 201 created or 400 duplicate if re-run

    def test_get_form_schema(self, client):
        login_as(client, "admin@company.vn", "Admin@123")
        res = client.get("/api/custom-fields/schema/customer")
        assert res.status_code == 200
        data = res.get_json()
        assert "fields" in data
        assert isinstance(data["fields"], list)
        assert any(f["key"] == "industry" for f in data["fields"])

    def test_custom_field_required_validation(self, client):
        login_as(client, "admin@company.vn", "Admin@123")

        # 'industry' is required for Customer in seed data
        res = client.post(
            "/api/customers",
            json={
                "name": "Khách hàng Thiếu Trường Bắt buộc",
                "phone": "0987654321",
                "custom_fields": {
                    "tax_code": "123456"
                    # 'industry' missing!
                },
            },
        )
        assert res.status_code == 400
        data = res.get_json()
        assert "errors" in data
        assert "industry" in data["errors"]

    def test_custom_field_type_validation(self, client):
        login_as(client, "admin@company.vn", "Admin@123")

        # 'budget_usd' must be a valid number
        res = client.post(
            "/api/customers",
            json={
                "name": "Khách hàng Sai Kiểu Số",
                "custom_fields": {
                    "industry": "Công nghệ",
                    "budget_usd": "abc_not_a_number",
                },
            },
        )
        assert res.status_code == 400
        assert "budget_usd" in res.get_json()["errors"]

        # 'contract_sign_date' must be valid YYYY-MM-DD date
        res = client.post(
            "/api/customers",
            json={
                "name": "Khách hàng Sai Kiểu Ngày",
                "custom_fields": {
                    "industry": "Công nghệ",
                    "contract_sign_date": "31/12/2026",
                },
            },
        )
        assert res.status_code == 400
        assert "contract_sign_date" in res.get_json()["errors"]

    def test_create_customer_with_custom_fields(self, client):
        login_as(client, "admin@company.vn", "Admin@123")

        res = client.post(
            "/api/customers",
            json={
                "name": "Công ty phần mềm Sài Gòn",
                "phone": "0909999888",
                "email": "info@saigonsoft.com",
                "address": "Quận 3, TP.HCM",
                "status": "Tiềm năng",
                "custom_fields": {
                    "industry": "Công nghệ",
                    "tax_code": "0312345678",
                    "budget_usd": 15000,
                    "contract_sign_date": "2026-10-31",
                },
            },
        )
        assert res.status_code == 201
        data = res.get_json()["customer"]
        assert data["name"] == "Công ty phần mềm Sài Gòn"
        assert data["custom_fields"]["industry"] == "Công nghệ"
        assert data["custom_fields"]["tax_code"] == "0312345678"

    def test_filter_customers_by_custom_fields(self, client):
        login_as(client, "admin@company.vn", "Admin@123")

        res = client.get("/api/customers?cf_industry=Công nghệ")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["items"]) >= 1
        for item in data["items"]:
            assert item["custom_fields"].get("industry") == "Công nghệ"

    def test_create_opportunity_with_custom_fields(self, client):
        login_as(client, "admin@company.vn", "Admin@123")

        # Get customer ID
        cust_res = client.get("/api/customers")
        cust_id = cust_res.get_json()["items"][0]["id"]

        res = client.post(
            "/api/opportunities",
            json={
                "title": "Dự án Nâng cấp Hạ tầng CNTT",
                "customer_id": cust_id,
                "value": 180000000,
                "stage": "Đàm phán",
                "expected_close_date": "2026-11-20",
                "custom_fields": {
                    "lead_source": "Website",
                    "margin_percent": 30,
                    "decision_maker": "Giám đốc Kỹ thuật",
                },
            },
        )
        assert res.status_code == 201
        opp = res.get_json()["opportunity"]
        assert opp["title"] == "Dự án Nâng cấp Hạ tầng CNTT"
        assert opp["custom_fields"]["lead_source"] == "Website"

    def test_export_customers_excel(self, client):
        login_as(client, "admin@company.vn", "Admin@123")
        res = client.get("/api/customers/export-excel")
        assert res.status_code == 200
        assert res.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(res.data) > 0

    def test_export_opportunities_excel(self, client):
        login_as(client, "admin@company.vn", "Admin@123")
        res = client.get("/api/opportunities/export-excel")
        assert res.status_code == 200
        assert res.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(res.data) > 0
