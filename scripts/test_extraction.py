from app.extraction import extract_contract_data

sample_text = """
SERVICE AGREEMENT

This agreement is entered into on 1 January 2026
between ABC Technologies Pvt Ltd and XYZ Solutions Ltd.

The agreement shall remain effective until
31 December 2026.

Either party may terminate this agreement by
providing 30 days written notice.

The service provider's total liability shall not
exceed the fees paid during the preceding 12 months.
"""

result = extract_contract_data(
    text=sample_text,
    page_number=1
)

print(result.model_dump_json(indent=2))