import pandas as pd

def create_template():
    df = pd.DataFrame(columns=["name", "tax_id", "website", "phone"])
    # Add some example data for the user to see
    df.loc[0] = ["Công ty TNHH ABC", "123456789", "abc.com", "0901234567"]
    df.loc[1] = ["Công ty Cổ phần XYZ", "987654321", "xyz.com", "0907654321"]

    template_path = "templates/customer_template.xlsx"
    import os
    os.makedirs("templates", exist_ok=True)
    df.to_excel(template_path, index=False)
    print(f"✅ Template created at: {template_path}")

if __name__ == "__main__":
    create_template()
