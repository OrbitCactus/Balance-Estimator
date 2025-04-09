from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
import re
import pytz

app = Flask(__name__)

# Needs to be updated to 17 April unit price figures.
historical_super_prices = [3.6869, 2.7430, 1.3841, 4.2233, 4.4292, 1.6935, 2.8227, 2.0241, 4.2103, 4.6761]
historical_income_prices = [2.7667, 2.5021, 1.4319, 5.5097, 3.0785, 1.6054, 1.5272, 0.9355, 3.8956, 3.5733]  # currently based on financial year for testing purposes, but will need to be updated to 17 April unit price figures.

def fetch_current_prices(account_type):
    australia_timezone = pytz.timezone("Australia/Sydney")
    today = datetime.now(australia_timezone).strftime("%d/%m/%Y")
    if account_type == "income":
        url = f"https://www.hesta.com.au/members/investments/income-stream-performance/jcr:content/par/investmentperformanc_1014712806.weekly?date={today}&dailyTransitionDate=22/10/2021"
    else:
        url = f"https://www.hesta.com.au/members/investments/super-performance/jcr:content/par/investmentperformanc.weekly?date={today}&dailyTransitionDate=22/10/2021"

    try:
        tables = pd.read_html(url)
        if len(tables) >= 2:
            df_combined = pd.concat([tables[0], tables[1]], ignore_index=True)
            names = df_combined.iloc[:10, 0].str.replace(r"[^a-zA-Z\s]", "", regex=True).tolist()
            prices = df_combined.iloc[:10, 3].replace('[\$,]', '', regex=True).astype(float).tolist()
            return names, prices
        else:
            return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    total_balance = 0
    current_names = []
    current_prices = []

    account_type = "super"
    if request.method == "POST":
        account_type = request.form.get("account_type", "super")

    current_names, current_prices = fetch_current_prices(account_type)

    if request.method == "POST" and current_prices:
        try:
            old_balance = float(request.form["old_balance"])
            allocations = [
                float(request.form[f"allocation{i}"]) / 100
                for i in range(10)
            ]

            historical_prices = historical_income_prices if account_type == "income" else historical_super_prices

            for i in range(10):
                alloc_amount = old_balance * allocations[i]
                old_unit_price = historical_prices[i]
                current_price = current_prices[i]

                old_units = alloc_amount / old_unit_price if old_unit_price != 0 else 0
                updated_balance = old_units * current_price

                if updated_balance > 0:
                    results.append({
                        "option": current_names[i],
                        "old_units": old_units,
                        "current_price": f"${current_price:.4f}",
                        "updated_balance": updated_balance
                    })

                    total_balance += updated_balance

        except Exception as e:
            print(f"Calculation error: {e}")

    return render_template("index.html", current_names=current_names, results=results, total_balance=total_balance)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
