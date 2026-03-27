from flask import Flask, request, redirect, url_for, render_template_string
import os

app = Flask(__name__)

# In-memory storage for expenses (for simplicity and to keep everything in one file)
expenses = []

# HTML template as a string to avoid needing a separate templates folder
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Basic Expense Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1, h2 {
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        input[type="text"], input[type="number"], input[type="date"] {
            padding: 8px;
            width: calc(100% - 16px);
            margin-top: 5px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        button {
            background-color: #28a745;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #218838;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
        }
        .total-row {
            font-weight: bold;
            background-color: #f8f9fa;
        }
        .meta-info {
            font-size: 0.8em;
            color: #777;
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Expense Tracker</h1>
        
        <div class="add-expense-section">
            <h2>Add New Expense</h2>
            <form action="{{ url_for('add_expense') }}" method="post">
                <div class="form-group">
                    <label for="date">Date:</label>
                    <input type="date" id="date" name="date" required>
                </div>
                <div class="form-group">
                    <label for="description">Description:</label>
                    <input type="text" id="description" name="description" placeholder="e.g., Groceries" required>
                </div>
                <div class="form-group">
                    <label for="amount">Amount ($):</label>
                    <input type="number" id="amount" name="amount" step="0.01" min="0" placeholder="0.00" required>
                </div>
                <button type="submit">Add Expense</button>
            </form>
        </div>

        <h2>Expense History</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
                {% for expense in expenses %}
                <tr>
                    <td>{{ expense.date }}</td>
                    <td>{{ expense.description }}</td>
                    <td>${{ "%.2f"|format(expense.amount) }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="3" style="text-align: center;">No expenses recorded yet.</td>
                </tr>
                {% endfor %}
            </tbody>
            <tfoot>
                <tr class="total-row">
                    <td colspan="2" style="text-align: right;">Total:</td>
                    <td>${{ "%.2f"|format(total_amount) }}</td>
                </tr>
            </tfoot>
        </table>

        <div class="meta-info">
            <p>Running on Pod: {{ hostname }}</p>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    # Render the main page with expenses
    hostname = os.environ.get('HOSTNAME', 'unknown')
    total_amount = sum(exp['amount'] for exp in expenses)
    return render_template_string(
        HTML_TEMPLATE, 
        expenses=expenses, 
        total_amount=total_amount, 
        hostname=hostname
    )

@app.route('/add', methods=['POST'])
def add_expense():
    # Handle the form submission to add an expense
    date = request.form.get('date')
    description = request.form.get('description')
    
    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        amount = 0.0

    if date and description and amount > 0:
        expenses.append({
            'date': date,
            'description': description,
            'amount': amount
        })
        
    # Redirect back to the main page
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
