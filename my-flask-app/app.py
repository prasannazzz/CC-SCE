from flask import Flask, request, redirect, url_for, render_template_string
import os
import uuid
import json
from datetime import datetime

app = Flask(__name__)

# In-memory storage for expenses
expenses = []

# Predefined categories
CATEGORIES = ['Food & Dining', 'Transportation', 'Housing', 'Entertainment', 'Shopping', 'Healthcare', 'Meditation','Other']

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expense Tracker Pro V2</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --glass-bg: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --primary-hover: #60a5fa;
            --accent: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            min-height: 100vh;
            color: var(--text-color);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 40px 20px;
        }

        .blob {
            position: fixed; top: 10%; left: 10%; width: 400px; height: 400px;
            background: #3b82f6; border-radius: 50%; filter: blur(150px);
            opacity: 0.3; animation: pulse 10s infinite alternate; z-index: -1;
        }
        .blob2 {
            position: fixed; bottom: 10%; right: 10%; width: 500px; height: 500px;
            background: #8b5cf6; border-radius: 50%; filter: blur(150px);
            opacity: 0.2; animation: pulse 12s infinite alternate-reverse; z-index: -1;
        }

        @keyframes pulse {
            0% { transform: scale(1) translate(0, 0); }
            100% { transform: scale(1.1) translate(30px, 30px); }
        }

        .container {
            width: 100%; max-width: 1000px;
            background: var(--glass-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border); border-radius: 24px;
            padding: 40px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            animation: slideUp 0.6s ease-out;
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h1 {
            font-size: 2.5rem; font-weight: 700; text-align: center; margin-bottom: 10px;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            text-align: center; color: var(--text-muted); margin-bottom: 40px;
        }

        h2 {
            font-size: 1.25rem; font-weight: 600; margin-bottom: 20px; color: var(--text-color);
            display: flex; justify-content: space-between; align-items: center;
        }

        .dashboard-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px;
        }

        .stat-card {
            background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border);
            border-radius: 16px; padding: 20px; text-align: center; transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); background: rgba(255,255,255,0.05); }
        .stat-card h3 { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 10px; font-weight: 400; }
        .stat-card .value { font-size: 2rem; font-weight: 700; color: var(--text-color); }
        .stat-card .value.accent { color: var(--accent); }

        .layout-grid { display: grid; grid-template-columns: 1fr 2fr; gap: 40px; }
        
        /* Mobile Responsiveness & Rendering Performance */
        @media (max-width: 800px) {
            .layout-grid { grid-template-columns: 1fr; gap: 20px; }
            .blob, .blob2 { display: none; } /* Removes heavy CSS blur on mobile to fix lag */
            body { padding: 15px 10px; }
            .container {
                padding: 20px;
                background: rgba(30, 41, 59, 0.95);
                backdrop-filter: none; /* Huge latency win on mobile */
                -webkit-backdrop-filter: none;
            }
            .dashboard-grid { grid-template-columns: 1fr; gap: 15px; margin-bottom: 25px; }
            h1 { font-size: 2rem; }
            .stat-card { padding: 15px; }
            .stat-card .value { font-size: 1.5rem; }
            .table-section { padding: 10px; }
            th, td { padding: 12px 8px; font-size: 0.85rem; }
            .chart-container { margin-top: 20px; padding: 10px; }
        }

        .form-section {
            background: rgba(15, 23, 42, 0.4); border-radius: 16px; padding: 24px; border: 1px solid var(--glass-border);
        }

        .form-group { margin-bottom: 15px; }
        label { display: block; font-size: 0.875rem; color: var(--text-muted); margin-bottom: 8px; font-weight: 600; }
        
        input, select {
            width: 100%; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--glass-border);
            color: var(--text-color); padding: 12px 16px; border-radius: 12px; font-size: 1rem;
            transition: all 0.3s ease; outline: none; font-family: inherit; appearance: none;
        }
        input:focus, select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25); }
        input::-webkit-calendar-picker-indicator { filter: invert(1); opacity: 0.6; cursor: pointer; }

        select option {
            background: var(--bg-color); color: var(--text-color);
        }

        button {
            width: 100%; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white;
            border: none; padding: 14px 24px; border-radius: 12px; font-size: 1rem; font-weight: 600;
            cursor: pointer; transition: all 0.3s; margin-top: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px -10px rgba(59, 130, 246, 0.7); }

        .chart-container {
            margin-top: 30px; background: rgba(15, 23, 42, 0.4); padding: 20px;
            border-radius: 16px; border: 1px solid var(--glass-border);
        }

        .table-section { overflow-x: auto; background: rgba(15, 23, 42, 0.2); border-radius: 16px; padding: 20px; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; }
        th, td { padding: 16px 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); }
        th { color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
        tbody tr { transition: all 0.2s; }
        tbody tr:hover { background: rgba(255, 255, 255, 0.03); border-radius: 8px; }
        
        .category-badge {
            background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; white-space: nowrap;
        }
        .amount-col { font-weight: 600; color: var(--text-color); text-align: right; }
        th.amount-col { text-align: right; }
        
        .btn-delete {
            background: transparent; color: var(--danger); padding: 6px 12px; font-size: 0.875rem;
            border: 1px solid rgba(239, 68, 68, 0.3); width: auto; margin: 0; box-shadow: none;
        }
        .btn-delete:hover {
            background: rgba(239, 68, 68, 0.1); transform: translateY(-1px); border-color: var(--danger); box-shadow: none;
        }

        .meta-info {
            margin-top: 40px; display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-muted);
        }
        .badge { background: rgba(59, 130, 246, 0.2); color: #93c5fd; padding: 4px 10px; border-radius: 20px; }
        
        .filters { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .filters a {
            text-decoration: none; color: var(--text-muted); padding: 6px 12px;
            border-radius: 20px; border: 1px solid var(--glass-border); font-size: 0.875rem; transition: all 0.2s;
        }
        .filters a.active { background: var(--primary); color: white; border-color: var(--primary); }
        .filters a:hover:not(.active) { background: rgba(255,255,255,0.1); color: var(--text-color); }
    </style>
</head>
<body hx-boost="true">
    <div class="blob"></div><div class="blob2"></div>

    <div class="container">
        <h1>Budget Tracker App/h1>
        <p class="subtitle">Manage your finances smartly</p>

        <!-- Dashboard Stats -->
        <div class="dashboard-grid">
            <div class="stat-card">
                <h3>Total Expenses</h3>
                <div class="value accent">${{ "%.2f"|format(total_amount) }}</div>
            </div>
            <div class="stat-card">
                <h3>Transactions</h3>
                <div class="value">{{ expenses|length }}</div>
            </div>
            <div class="stat-card">
                <h3>Highest Expense</h3>
                <div class="value">${{ "%.2f"|format(highest_expense) }}</div>
            </div>
        </div>

        <div class="layout-grid">
            <!-- Form & Charts -->
            <div class="left-panel">
                <div class="form-section">
                    <h2>Add Expense</h2>
                    <form action="{{ url_for('add_expense') }}" method="post">
                        <div class="form-group">
                            <label>Date</label>
                            <input type="date" name="date" required value="{{ today }}">
                        </div>
                        <div class="form-group">
                            <label>Category</label>
                            <select name="category" required>
                                {% for cat in categories %}
                                <option value="{{ cat }}">{{ cat }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Description (Optional)</label>
                            <input type="text" name="description" placeholder="e.g., Grocery run">
                        </div>
                        <div class="form-group">
                            <label>Amount ($)</label>
                            <input type="number" name="amount" step="0.01" min="0" required placeholder="0.00">
                        </div>
                        <button type="submit">Record Expense</button>
                    </form>
                </div>

                {% if expenses|length > 0 %}
                <div class="chart-container">
                    <canvas id="expenseChart" width="400" height="300"></canvas>
                </div>
                {% endif %}
            </div>

            <!-- Table -->
            <div class="right-panel">
                <h2>
                    Transactions
                    {% if current_filter %}
                    <span style="font-size: 0.9rem; font-weight: normal; color: var(--text-muted)">
                        ({{ current_filter }}) <a href="/" style="color: var(--primary); text-decoration: none; margin-left: 10px;">Clear Filter</a>
                    </span>
                    {% endif %}
                </h2>
                
                {% if used_categories|length > 0 %}
                <div class="filters">
                    <span style="color: var(--text-muted); font-size: 0.875rem; align-self: center;">Filter:</span>
                    <a href="/" class="{{ 'active' if not current_filter else '' }}">All</a>
                    {% for cat in used_categories %}
                    <a href="/?filter={{ cat|urlencode }}" class="{{ 'active' if current_filter == cat else '' }}">{{ cat }}</a>
                    {% endfor %}
                </div>
                {% endif %}

                <div class="table-section">
                    <table>
                        <thead>
                            <tr>
                                <th>Details</th>
                                <th>Category</th>
                                <th class="amount-col">Amount</th>
                                <th style="text-align: right;">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for expense in displayed_expenses %}
                            <tr>
                                <td>
                                    <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-color);">{{ expense.description or 'N/A' }}</div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted);">{{ expense.date }}</div>
                                </td>
                                <td><span class="category-badge">{{ expense.category }}</span></td>
                                <td class="amount-col">${{ "%.2f"|format(expense.amount) }}</td>
                                <td style="text-align: right;">
                                    <form action="{{ url_for('delete_expense', exp_id=expense.id) }}" method="post" style="margin:0;">
                                        <!-- Keep filter query param if available -->
                                        {% if current_filter %}
                                        <input type="hidden" name="filter" value="{{ current_filter }}">
                                        {% endif %}
                                        <button type="submit" class="btn-delete">Delete</button>
                                    </form>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 40px 0;">
                                    {% if current_filter %}
                                    No expenses found for this category.
                                    {% else %}
                                    No expenses recorded yet. Start tracking!
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="meta-info">
            <span>Server Instance</span>
            <span class="badge">{{ hostname }}</span>
        </div>
    </div>

    <!-- Chart Logic -->
    <script>
        {% if expenses|length > 0 %}
        const ctx = document.getElementById('expenseChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: {{ chart_labels|safe }},
                    datasets: [{
                        data: {{ chart_data|safe }},
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(75, 85, 99, 0.8)'
                        ],
                        borderWidth: 1,
                        borderColor: 'rgba(30, 41, 59, 1)',
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            position: 'bottom', 
                            labels: { 
                                color: '#f8fafc', 
                                font: { family: 'Inter', size: 12 },
                                padding: 20
                            } 
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed !== null) {
                                        label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed);
                                    }
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
        }
        {% endif %}
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    # Render the main page
    hostname = os.environ.get('HOSTNAME', 'unknown')
    today = datetime.now().strftime('%Y-%m-%d')
    filter_cat = request.args.get('filter')

    # Basic stats
    total_amount = sum(exp['amount'] for exp in expenses)
    highest_expense = max((exp['amount'] for exp in expenses), default=0.0) if expenses else 0.0
    
    # Categories that actually have expenses (for filtering)
    used_categories = sorted(list(set(exp['category'] for exp in expenses)))

    # Filter expenses if requested
    if filter_cat:
        displayed_expenses = [e for e in expenses if e['category'] == filter_cat]
    else:
        # Sort newest first based on date
        displayed_expenses = sorted(expenses, key=lambda x: x['date'], reverse=True)

    # Chart data (sum by category of all expenses)
    category_totals = {}
    for exp in expenses:
        category_totals[exp['category']] = category_totals.get(exp['category'], 0.0) + exp['amount']
    
    chart_labels = json.dumps(list(category_totals.keys()))
    chart_data = json.dumps(list(category_totals.values()))

    return render_template_string(
        HTML_TEMPLATE, 
        expenses=expenses, 
        displayed_expenses=displayed_expenses,
        categories=CATEGORIES,
        used_categories=used_categories,
        current_filter=filter_cat,
        total_amount=total_amount, 
        highest_expense=highest_expense,
        hostname=hostname,
        today=today,
        chart_labels=chart_labels,
        chart_data=chart_data
    )

@app.route('/add', methods=['POST'])
def add_expense():
    date = request.form.get('date')
    category = request.form.get('category')
    description = request.form.get('description', '').strip()
    
    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        amount = 0.0

    if date and category and amount > 0:
        expenses.append({
            'id': str(uuid.uuid4()),
            'date': date,
            'category': category,
            'description': description if description else category, # fallback to category name
            'amount': amount
        })
        
    return redirect(url_for('index'))

@app.route('/delete/<exp_id>', methods=['POST'])
def delete_expense(exp_id):
    global expenses
    expenses = [exp for exp in expenses if exp['id'] != exp_id]
    
    # Redirect back to the same filter if it was active
    filter_cat = request.form.get('filter')
    if filter_cat:
        return redirect(url_for('index', filter=filter_cat))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
