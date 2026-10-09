"""
app/lead_convert.py — Chuyển đổi Lead thành Khách hàng, Người liên hệ và Cơ hội bán hàng (SCRUM-85)

Một thao tác đơn, đồng thời:
  1. Tạo dbo.customers (khách hàng doanh nghiệp)
  2. Tạo dbo.lead_contacts (người liên hệ của lead, liên kết vào khách hàng mới)
  3. Tạo dbo.opportunities (cơ hội bán hàng)
  4. Chuyển lead sang trạng thái 'Đã chuyển đổi' → không sửa được nữa
  5. Gắn lại toàn bộ lead_activities → cũng được nhân bản vào customer_interactions
"""
import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db


def _now_ms() -> int:
    return int(time.time() * 1000)


def ensure_lead_contacts_table(conn) -> None:
    """Bảng người liên hệ (contact person) của khách hàng doanh nghiệp."""
    cur = conn.cursor()
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'lead_contacts' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.lead_contacts (
                id              INT             IDENTITY(1,1) PRIMARY KEY,
                customer_id     INT             NOT NULL,
                -- FK → dbo.customers.id
                lead_id         INT             NOT NULL,
                -- FK → dbo.leads.id (nguồn gốc)
                full_name       NVARCHAR(255)   NOT NULL,
                email           NVARCHAR(255)   NULL,
                phone           NVARCHAR(50)    NULL,
                position        NVARCHAR(255)   NULL,
                is_primary      BIT             NOT NULL DEFAULT 1,
                created_at      BIGINT          NOT NULL,
                CONSTRAINT FK_lead_contacts_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id),
                CONSTRAINT FK_lead_contacts_lead     FOREIGN KEY (lead_id)     REFERENCES dbo.leads(id)
            );
        END
        """
    )
    conn.commit()


def convert_lead_to_customer(
    lead_id: int,
    converted_by: int,
    # Thông tin khách hàng doanh nghiệp (company)
    company_name: str | None = None,
    company_phone: str = "",
    company_email: str = "",
    company_address: str = "",
    # Thông tin cơ hội bán hàng
    opportunity_title: str | None = None,
    opportunity_value: float = 0.0,
    opportunity_stage: str = "Mới tạo",
    opportunity_stage_key: str = "new",
    opportunity_expected_close_date: str = "",
    # Thông tin người liên hệ (contact)
    contact_position: str = "",
) -> dict[str, Any]:
    """
    Chuyển đổi Lead thành Khách hàng + Người liên hệ + Cơ hội bán hàng (SCRUM-85).

    - Dữ liệu từ lead (tên, email, phone) được tự động chuyển sang → không phải nhập lại.
    - Lead chuyển sang 'Đã chuyển đổi' và bị khóa chỉnh sửa.
    - Toàn bộ lead_activities được nhân bản sang customer_interactions.

    Raises:
        LookupError: Nếu lead không tồn tại.
        ValueError: Nếu lead đã được chuyển đổi rồi.
    """
    from app.leads import (
        LEAD_STATUS_CONVERTED,
        _get_lead_raw,
        _log_activity,
        ensure_leads_tables,
    )
    from app.periodic_care import ensure_periodic_care_tables

    conn = get_db()
    ensure_leads_tables(conn)
    ensure_periodic_care_tables(conn)
    ensure_lead_contacts_table(conn)

    lead = _get_lead_raw(conn, lead_id)
    if not lead:
        raise LookupError("lead_not_found")
    if lead["status"] == LEAD_STATUS_CONVERTED:
        raise ValueError("lead_already_converted")

    now = _now_ms()

    # 1. Tạo Khách hàng doanh nghiệp (dbo.customers)
    # Ưu tiên dùng company_name, fallback về tên lead
    cust_name = (company_name or lead["company"] or lead["full_name"]).strip()
    if not cust_name:
        cust_name = lead["full_name"]

    cust_phone = (company_phone or lead.get("phone") or "").strip()
    cust_email = (company_email or lead.get("email") or "").strip()
    cust_address = company_address.strip()

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.customers (name, phone, email, address, status, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (cust_name, cust_phone, cust_email, cust_address, "Mới", converted_by, now, now),
    )
    conn.commit()

    new_cust = fetch_one(
        conn,
        "SELECT MAX(id) AS id FROM dbo.customers WHERE name = ? AND created_by = ?",
        (cust_name, converted_by),
    )
    customer_id = new_cust["id"]

    # 2. Tạo Người liên hệ (dbo.lead_contacts)
    cur.execute(
        """
        INSERT INTO dbo.lead_contacts (customer_id, lead_id, full_name, email, phone, position, is_primary, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            customer_id,
            lead_id,
            lead["full_name"],
            lead.get("email") or "",
            lead.get("phone") or "",
            contact_position.strip(),
            now,
        ),
    )
    conn.commit()

    # 3. Tạo Cơ hội bán hàng (dbo.opportunities)
    opp_title = (opportunity_title or f"Cơ hội từ lead: {lead['full_name']}").strip()

    cur.execute(
        """
        INSERT INTO dbo.opportunities
            (title, customer_id, value, stage, stage_key, expected_close_date, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            opp_title,
            customer_id,
            opportunity_value,
            opportunity_stage,
            opportunity_stage_key,
            opportunity_expected_close_date,
            converted_by,
            now,
            now,
        ),
    )
    conn.commit()

    opp_row = fetch_one(
        conn,
        "SELECT MAX(id) AS id FROM dbo.opportunities WHERE customer_id = ? AND created_by = ?",
        (customer_id, converted_by),
    )
    opportunity_id = opp_row["id"]

    # 4. Chuyển trạng thái lead → 'Đã chuyển đổi' (bị khóa)
    cur.execute(
        """
        UPDATE dbo.leads
        SET status = ?, converted_at = ?, customer_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (LEAD_STATUS_CONVERTED, now, customer_id, now, lead_id),
    )
    conn.commit()

    # 5. Nhân bản lịch sử lead_activities → customer_interactions
    activities = fetch_all(
        conn,
        """
        SELECT activity_type, description, performed_by, created_at
        FROM dbo.lead_activities
        WHERE lead_id = ?
        ORDER BY id ASC
        """,
        (lead_id,),
    )
    for act in activities:
        interaction_type = _map_activity_to_interaction(act["activity_type"])
        desc = act["description"] or ""
        cur.execute(
            """
            INSERT INTO dbo.customer_interactions
                (customer_id, interaction_type, notes, created_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                interaction_type,
                f"[Từ lead #{lead_id}] {desc}",
                act["performed_by"] or converted_by,
                act["created_at"],
            ),
        )
    conn.commit()

    # 6. Ghi thêm activity chuyển đổi
    _log_activity(
        conn,
        lead_id,
        "converted",
        f"Lead chuyển đổi thành Khách hàng #{customer_id} và Cơ hội #{opportunity_id}.",
        converted_by,
    )
    conn.commit()

    return {
        "lead_id": lead_id,
        "customer_id": customer_id,
        "opportunity_id": opportunity_id,
        "customer_name": cust_name,
        "opportunity_title": opp_title,
        "contact": {
            "full_name": lead["full_name"],
            "email": lead.get("email") or "",
            "phone": lead.get("phone") or "",
            "position": contact_position.strip(),
        },
        "converted_at": now,
        "activities_migrated": len(activities),
    }


def _map_activity_to_interaction(activity_type: str) -> str:
    """Ánh xạ loại hoạt động của lead sang loại tương tác của khách hàng."""
    mapping = {
        "created": "Tạo từ lead",
        "assigned": "Phân công từ lead",
        "accepted": "Nhận chăm sóc",
        "rejected": "Từ chối phân công",
        "sla_breached": "Cảnh báo SLA",
        "converted": "Chuyển đổi thành khách hàng",
        "note": "Ghi chú",
        "updated": "Cập nhật thông tin",
    }
    return mapping.get(activity_type, activity_type)


def get_lead_contact(customer_id: int) -> list[dict[str, Any]]:
    """Lấy danh sách người liên hệ của một khách hàng doanh nghiệp."""
    conn = get_db()
    ensure_lead_contacts_table(conn)
    return fetch_all(
        conn,
        """
        SELECT lc.id, lc.customer_id, lc.lead_id, lc.full_name,
               lc.email, lc.phone, lc.position, lc.is_primary, lc.created_at
        FROM dbo.lead_contacts lc
        WHERE lc.customer_id = ?
        ORDER BY lc.is_primary DESC, lc.id ASC
        """,
        (customer_id,),
    )
