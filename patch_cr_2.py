import re

with open("backend/app/crud/crud_dashboard.py", "r") as f:
    content = f.read()

# Replace rd_maturity_dates dict with processed_rds list
old_dict = """    rd_maturity_dates = {
        rd.id: rd.start_date + relativedelta(months=rd.tenure_months)
        for rd in all_rds
    }"""
new_list = """    # Pre-calculate RD maturity dates to avoid O(N) recalculation inside the daily loop
    processed_rds = [
        (rd, rd.start_date + relativedelta(months=rd.tenure_months))
        for rd in all_rds
    ]"""
content = content.replace(old_dict, new_list)

# Replace the loop unpacking
old_loop = """                for rd in all_rds:
                    if rd.start_date > current_day:
                        continue

                    rd_maturity_date = rd_maturity_dates.get(rd.id)"""
new_loop = """                for rd, rd_maturity_date in processed_rds:
                    if rd.start_date > current_day:
                        continue"""
content = content.replace(old_loop, new_loop)

with open("backend/app/crud/crud_dashboard.py", "w") as f:
    f.write(content)
