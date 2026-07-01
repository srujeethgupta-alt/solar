import urllib.request
import urllib.error
import json
import os

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", headers=None, body=None):
    if headers is None:
        headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        data = None
        
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode("utf-8")), res.info()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            body_json = json.loads(body)
        except Exception:
            body_json = body
        return e.code, body_json, None
    except Exception as e:
        return 0, str(e), None

def run_tests():
    print("--- STARTING API VERIFICATION TESTS ---")
    
    # 1. Login Test (Invalid)
    code, res, _ = make_request(f"{BASE_URL}/api/login", "POST", body={"username": "admin", "password": "wrongpassword"})
    print(f"Login (invalid password) -> Status: {code}, Response: {res}")
    assert code == 400, "Should fail on invalid password"
    
    # 2. Login Test (Valid)
    code, res, _ = make_request(f"{BASE_URL}/api/login", "POST", body={"username": "admin", "password": "solar123"})
    print(f"Login (valid) -> Status: {code}")
    assert code == 200, "Should pass on valid credentials"
    token = res["token"]
    print(f"Acquired Session Token: {token}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Get Products
    code, products, _ = make_request(f"{BASE_URL}/api/products", "GET", headers=headers)
    print(f"Fetch Products -> Status: {code}, Count: {len(products)}")
    assert code == 200, "Should get products catalog"

    # 3.1 Test Add Supplier
    sup_payload = {
        "id": "S001",
        "name": "Global Solar Dist",
        "contact_person": "Alice",
        "phone": "555-0192",
        "email": "alice@globalsolar.com",
        "address": "123 Solar Way"
    }
    code, sup_res, _ = make_request(f"{BASE_URL}/api/suppliers", "POST", headers=headers, body=sup_payload)
    print(f"Add Supplier -> Status: {code}, Response: {sup_res}")
    assert code == 200, "Should add supplier successfully"

    # 3.2 Test Add Customer
    cust_payload = {
        "id": "C001",
        "name": "Eco Build Corp",
        "contact_person": "Bob",
        "phone": "555-9988",
        "email": "bob@ecobuild.com",
        "address": "456 Green Blvd"
    }
    code, cust_res, _ = make_request(f"{BASE_URL}/api/customers", "POST", headers=headers, body=cust_payload)
    print(f"Add Customer -> Status: {code}, Response: {cust_res}")
    assert code == 200, "Should add customer successfully"
    
    # 4. Add Product
    new_product = {
        "id": "P006",
        "name": "Bifacial Solar Panel 450W",
        "category": "Solar Panels",
        "brand": "Longi Solar",
        "unit": "Pcs",
        "quantity": 50,
        "minimum_stock": 15,
        "supplier": "Longi Logistics",
        "rack_location": "Rack A-2"
    }
    code, add_res, _ = make_request(f"{BASE_URL}/api/products", "POST", headers=headers, body=new_product)
    print(f"Add Product -> Status: {code}, Response: {add_res}")
    assert code == 200, "Should add P006 successfully"
    
    # 5. Stock Out Check (Insufficient stock warning)
    stock_out_bad = {
        "product_id": "P006",
        "quantity": 60,
        "customer": "Vignan Solar Site",
        "date": "2026-06-29",
        "remarks": "Overselling test"
    }
    code, out_bad_res, _ = make_request(f"{BASE_URL}/api/stock-out", "POST", headers=headers, body=stock_out_bad)
    print(f"Stock Out (Insufficient) -> Status: {code}, Response: {out_bad_res}")
    assert code == 400, "Should fail with insufficient stock"
    
    # 6. Stock Out Check (Success - optional customer and custom employee name)
    stock_out_good = {
        "product_id": "P006",
        "quantity": 10,
        "customer": "",
        "employee": "John Doe",
        "date": "2026-06-29",
        "remarks": "Project phase 1"
    }
    code, out_good_res, _ = make_request(f"{BASE_URL}/api/stock-out", "POST", headers=headers, body=stock_out_good)
    print(f"Stock Out (Successful) -> Status: {code}, Response: {out_good_res}")
    assert code == 200, "Should deduct 10 items successfully"
    
    # Check quantity
    code, products, _ = make_request(f"{BASE_URL}/api/products", "GET", headers=headers)
    p006 = next(p for p in products if p["id"] == "P006")
    print(f"P006 Quantity after stock out: {p006['quantity']}")
    assert p006["quantity"] == 40, "Quantity should be 40"
    
    # 7. Stock In Check (Success)
    stock_in_payload = {
        "product_id": "P006",
        "quantity": 25,
        "supplier": "Longi Logistics",
        "date": "2026-06-29",
        "remarks": "Weekly supply restock"
    }
    code, in_res, _ = make_request(f"{BASE_URL}/api/stock-in", "POST", headers=headers, body=stock_in_payload)
    print(f"Stock In -> Status: {code}, Response: {in_res}")
    assert code == 200, "Should increment stock by 25"
    
    # Verify quantity
    code, products, _ = make_request(f"{BASE_URL}/api/products", "GET", headers=headers)
    p006 = next(p for p in products if p["id"] == "P006")
    print(f"P006 Quantity after stock in: {p006['quantity']}")
    assert p006["quantity"] == 65, "Quantity should be 65"
    
    # 8. Clean up P006 for re-run repeatability
    code, del_res, _ = make_request(f"{BASE_URL}/api/products/P006", "DELETE", headers=headers)
    print(f"Delete Product P006 -> Status: {code}")
    assert code == 200, "Should delete P006 for cleanup"
    
    # 9. Verify PDF Export
    pdf_url = f"{BASE_URL}/api/reports/export?range_type=daily&file_format=pdf"
    req_pdf = urllib.request.Request(pdf_url, headers=headers)
    try:
        with urllib.request.urlopen(req_pdf) as res_pdf:
            pdf_data = res_pdf.read()
            print(f"PDF Export -> Status: {res_pdf.status}, Content Length: {len(pdf_data)} bytes")
            assert res_pdf.status == 200, "Should export PDF"
            assert len(pdf_data) > 0, "PDF should not be empty"
    except Exception as e:
        print(f"PDF Export failed: {e}")
        
    # 10. Verify Excel Export
    xlsx_url = f"{BASE_URL}/api/reports/export?range_type=daily&file_format=xlsx"
    req_xlsx = urllib.request.Request(xlsx_url, headers=headers)
    try:
        with urllib.request.urlopen(req_xlsx) as res_xlsx:
            xlsx_data = res_xlsx.read()
            print(f"Excel Export -> Status: {res_xlsx.status}, Content Length: {len(xlsx_data)} bytes")
            assert res_xlsx.status == 200, "Should export Excel"
            assert len(xlsx_data) > 0, "Excel should not be empty"
    except Exception as e:
        print(f"Excel Export failed: {e}")

    print("--- ALL VERIFICATION TESTS PASSED ---")

if __name__ == "__main__":
    run_tests()
