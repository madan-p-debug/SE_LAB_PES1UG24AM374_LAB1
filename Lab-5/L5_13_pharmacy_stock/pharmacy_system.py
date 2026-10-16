"""Pharmacy prescription and stock tracker.

Records medicine stock and expiry dates, looks up patients and their
allergies in a small in-memory database, dispenses prescriptions and
exports them to a JSON file.
"""
import json
import sqlite3
from datetime import datetime

# Global state
conn = sqlite3.connect(":memory:")
stock = {}
prescriptions = []


def setup_database():
    """Create the patients table and insert the sample patients."""
    cur = conn.cursor()
    cur.execute("CREATE TABLE patients (id TEXT, name TEXT, allergy TEXT)")
    cur.execute("INSERT INTO patients VALUES ('P1', 'Kavya', 'penicillin')")
    cur.execute("INSERT INTO patients VALUES ('P2', 'Arjun', 'none')")
    cur.execute("INSERT INTO patients VALUES ('P3', 'Meena', 'ibuprofen')")
    conn.commit()


def find_patient(name):
    """Return a list of (id, allergy) rows for patients called ``name``."""
    cur = conn.cursor()
    query = "SELECT id, allergy FROM patients WHERE name = ?"
    return cur.execute(query, (name,)).fetchall()


def add_stock(drug, units, expiry, batch_log=None):
    """Add ``units`` of ``drug`` to stock and return the batch log length.

    When the drug is already stocked, the earlier of the two expiry dates is
    kept so that older units are never mislabelled with a later date.
    """
    if units <= 0:
        raise ValueError(
            f"Cannot add {units} units of {drug}: must be positive")
    if batch_log is None:
        batch_log = []
    current = stock.get(drug)
    if current:
        units += current["units"]
        expiry = min(expiry, current["expiry"])
    stock[drug] = {"units": units, "expiry": expiry}
    batch_log.append((drug, units))
    return len(batch_log)


def dispense(patient_name, drug, units):
    """Dispense ``units`` of ``drug`` to a patient; return True on success."""
    patients = find_patient(patient_name)
    if not patients:
        print("Unknown patient:", patient_name)
        return False
    patient_id, allergy = patients[0]
    if drug.lower() == allergy.lower():
        print("Allergy warning for", patient_name)
        return False
    item = stock.get(drug)
    if item is None:
        print("Drug not in stock:", drug)
        return False
    if datetime.strptime(item["expiry"], "%Y-%m-%d") < datetime.now():
        print("Drug expired:", drug)
        return False
    if units <= 0 or item["units"] < units:
        print("Insufficient stock for", drug, "- available:", item["units"])
        return False
    item["units"] -= units
    prescriptions.append({"patient": patient_id, "drug": drug, "units": units,
                          "time": str(datetime.now())})
    return True


def expiring_soon(days=30):
    """Return drugs expiring within ``days`` days (or already expired)."""
    soon = []
    for drug, item in stock.items():
        exp = datetime.strptime(item["expiry"], "%Y-%m-%d")
        if (exp - datetime.now()).days < days:
            soon.append(drug)
    return soon


def export_prescriptions(file="prescriptions.json"):
    """Write all prescriptions to ``file`` as JSON."""
    with open(file, "w", encoding="utf-8") as out:
        json.dump(prescriptions, out)


def load_stock(file="stock.json"):
    """Load stock from ``file`` if it exists and is valid JSON."""
    try:
        with open(file, encoding="utf-8") as src:
            loaded = json.load(src)
    except FileNotFoundError:
        print("No saved stock file found, starting with empty stock.")
        return
    except json.JSONDecodeError as err:
        print("Stock file is corrupt, starting with empty stock:", err)
        return
    stock.clear()
    stock.update(loaded)


def print_stock():
    """Print every drug with its units and expiry date."""
    print("Pharmacy Stock")
    for drug, item in stock.items():
        print(drug, "->", item["units"], "units, expires", item["expiry"])


def main():
    """Run the demo scenario."""
    setup_database()
    load_stock()
    add_stock("Paracetamol", 100, "2027-03-01")
    add_stock("Amoxicillin", 20, "2025-12-31")
    add_stock("Penicillin", 50, "2027-01-15")
    try:
        add_stock("Ibuprofen", -15, "2026-11-30")
    except ValueError as err:
        print("Stock error:", err)
    print("Arjun gets Amoxicillin:", dispense("Arjun", "Amoxicillin", 30))
    print("Kavya gets Penicillin:", dispense("Kavya", "Penicillin", 10))
    print("Meena gets ibuprofen:", dispense("Meena", "ibuprofen", 2))
    print("Unknown patient:", dispense("Ghost", "Paracetamol", 5))
    name = input("Patient name to look up (Enter for Arjun): ") or "Arjun"
    print("Lookup result:", find_patient(name))
    print("Expiring within 30 days:", expiring_soon())
    export_prescriptions()
    print_stock()


if __name__ == "__main__":
    main()
