import json
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import matplotlib.pyplot as plt

FILE_NAME = "expenses.json"


def load_expenses():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    return []


def save_expenses(expenses):
    with open(FILE_NAME, "w") as file:
        json.dump(expenses, file, indent=4)


def launch_gui():
    expenses = load_expenses()
    budget_limit = [None]  # Mutable container for budget inside nested functions

    root = tk.Tk()
    root.title("Expense Tracker GUI")
    root.geometry("900x600")
    root.config(bg="#f0f0f0")
    root.resizable(False, False)

    # --- Helper functions ---

    def refresh_listbox(filtered=None):
        listbox.delete(0, tk.END)
        display_list = filtered if filtered is not None else expenses

        for i, exp in enumerate(display_list):
            listbox.insert(
                tk.END,
                f"{i+1}. ${exp['amount']:.2f} | {exp['category']} | {exp['note']} | {exp['date']}",
            )
        update_budget_status()

    def update_budget_status():
        if budget_limit[0] is None:
            budget_label.config(text="Budget limit: Not set", fg="black")
            return
        total_spent = sum(exp["amount"] for exp in expenses)
        budget_label.config(
            text=f"Budget: ${budget_limit[0]:.2f} | Spent: ${total_spent:.2f}",
            fg="red" if total_spent > budget_limit[0] else "green",
        )
        if total_spent > budget_limit[0]:
            messagebox.showwarning("Budget Alert", "You have exceeded your budget limit!")
        elif total_spent > 0.9 * budget_limit[0]:
            messagebox.showinfo("Budget Warning", "You are close to exceeding your budget limit.")

    # New function: Custom popup for add/edit expense
    def expense_form_popup(title, initial=None):
        """
        Show a popup window with entries for amount, category, note, date.
        If initial dict provided, fill entries with initial values.
        Returns dict with keys: amount (float), category (str), note (str), date (str) on success,
        or None if cancelled.
        """
        popup = tk.Toplevel(root)
        popup.title(title)
        popup.geometry("350x300")
        popup.resizable(False, False)
        popup.grab_set()  # modal
        popup.transient(root)

        # Labels and entries
        tk.Label(popup, text="Amount ($):").pack(pady=(15, 0))
        amount_var = tk.StringVar(value=str(initial["amount"]) if initial else "")
        amount_entry = tk.Entry(popup, textvariable=amount_var)
        amount_entry.pack(pady=5)

        tk.Label(popup, text="Category:").pack(pady=(10, 0))
        category_var = tk.StringVar(value=initial["category"] if initial else "")
        category_entry = tk.Entry(popup, textvariable=category_var)
        category_entry.pack(pady=5)

        tk.Label(popup, text="Note (optional):").pack(pady=(10, 0))
        note_var = tk.StringVar(value=initial["note"] if initial else "")
        note_entry = tk.Entry(popup, textvariable=note_var)
        note_entry.pack(pady=5)

        tk.Label(popup, text="Date (YYYY-MM-DD) or leave blank for today:").pack(pady=(10, 0))
        date_var = tk.StringVar(value=initial["date"] if initial else "")
        date_entry = tk.Entry(popup, textvariable=date_var)
        date_entry.pack(pady=5)

        result = {}

        def on_submit():
            try:
                amt = amount_var.get().strip()
                if not amt:
                    messagebox.showerror("Error", "Amount is required.", parent=popup)
                    return
                amount = float(amt)
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive.", parent=popup)
                    return

                category = category_var.get().strip()
                if not category:
                    messagebox.showerror("Error", "Category cannot be empty.", parent=popup)
                    return

                note = note_var.get().strip()

                date_str = date_var.get().strip()
                if not date_str:
                    date_str = datetime.today().strftime("%Y-%m-%d")
                else:
                    datetime.strptime(date_str, "%Y-%m-%d")  # Validate format

                result.update({
                    "amount": amount,
                    "category": category,
                    "note": note,
                    "date": date_str,
                })
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}", parent=popup)

        submit_btn = tk.Button(popup, text="Submit", command=on_submit, bg="#4CAF50", fg="white")
        submit_btn.pack(pady=15)

        amount_entry.focus()
        root.wait_window(popup)
        return result if result else None

    def add_expense_gui():
        data = expense_form_popup("Add Expense")
        if data:
            expenses.append(data)
            save_expenses(expenses)
            refresh_listbox()
            messagebox.showinfo("Success", "Expense added!")

    def edit_expense_gui():
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "No expense selected")
            return
        idx = selected[0]
        exp = expenses[idx]
        data = expense_form_popup("Edit Expense", initial=exp)
        if data:
            expenses[idx] = data
            save_expenses(expenses)
            refresh_listbox()
            messagebox.showinfo("Success", "Expense updated!")

    def delete_expense_gui():
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "No expense selected")
            return
        idx = selected[0]
        removed = expenses.pop(idx)
        save_expenses(expenses)
        refresh_listbox()
        messagebox.showinfo(
            "Deleted", f"Deleted expense: ${removed['amount']:.2f} - {removed['category']}"
        )

    def sort_expenses(key):
        if key == "Date":
            expenses.sort(key=lambda x: x["date"])
        elif key == "Amount":
            expenses.sort(key=lambda x: x["amount"])
        elif key == "Category":
            expenses.sort(key=lambda x: x["category"].lower())
        refresh_listbox()

    def search_expenses(event=None):
        query = search_var.get().strip().lower()
        if not query:
            refresh_listbox()
            return
        filtered = [
            exp
            for exp in expenses
            if query in exp["category"].lower() or query in exp["note"].lower()
        ]
        refresh_listbox(filtered)

    def set_budget():
        try:
            val = tk.simpledialog.askstring("Set Budget", "Enter monthly budget amount ($):", parent=root)
            if val is None:
                return
            b = float(val)
            if b <= 0:
                messagebox.showerror("Error", "Budget must be positive.")
                return
            budget_limit[0] = b
            update_budget_status()
            messagebox.showinfo("Budget Set", f"Budget set to ${b:.2f}")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid budget: {e}")

    def export_csv_gui():
        if not expenses:
            messagebox.showwarning("Warning", "No expenses to export.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export expenses as CSV",
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="") as csvfile:
                fieldnames = ["amount", "category", "note", "date"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for exp in expenses:
                    writer.writerow(exp)
            messagebox.showinfo("Exported", f"Expenses exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def import_csv_gui():
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")], title="Import expenses from CSV"
        )
        if not file_path:
            return
        try:
            with open(file_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                count = 0
                for row in reader:
                    try:
                        amount = float(row["amount"])
                        category = row["category"].strip()
                        note = row.get("note", "")
                        date_str = row.get("date", datetime.today().strftime("%Y-%m-%d"))
                        datetime.strptime(date_str, "%Y-%m-%d")
                        expense = {
                            "amount": amount,
                            "category": category,
                            "note": note,
                            "date": date_str,
                        }
                        expenses.append(expense)
                        count += 1
                    except Exception:
                        continue
            save_expenses(expenses)
            refresh_listbox()
            messagebox.showinfo("Imported", f"Imported {count} expenses from CSV.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {e}")

    def show_category_pie_chart():
        if not expenses:
            messagebox.showwarning("No Data", "No expenses to chart.")
            return
        summary = {}
        for exp in expenses:
            summary[exp["category"]] = summary.get(exp["category"], 0) + exp["amount"]
        categories = list(summary.keys())
        amounts = list(summary.values())

        plt.figure(figsize=(6, 6))
        plt.pie(
            amounts,
            labels=categories,
            autopct="%1.1f%%",
            startangle=140,
            colors=plt.cm.Paired.colors,
        )
        plt.title("Spending by Category")
        plt.show()

    # --- GUI Layout ---

    title_lbl = tk.Label(
        root,
        text="Expense Tracker",
        font=("Helvetica", 22, "bold"),
        bg="#f0f0f0",
        fg="#333333",
    )
    title_lbl.pack(pady=10)

    top_frame = tk.Frame(root, bg="#f0f0f0")
    top_frame.pack(pady=5)

    tk.Label(top_frame, text="Search:", bg="#f0f0f0", font=("Arial", 12)).pack(side=tk.LEFT)
    search_var = tk.StringVar()
    search_entry = tk.Entry(top_frame, textvariable=search_var, width=30, font=("Arial", 12))
    search_entry.pack(side=tk.LEFT, padx=5)
    search_entry.bind("<KeyRelease>", search_expenses)

    tk.Label(top_frame, text="Sort by:", bg="#f0f0f0", font=("Arial", 12)).pack(side=tk.LEFT, padx=(15, 5))
    sort_options = ttk.Combobox(top_frame, values=["Date", "Amount", "Category"], state="readonly", width=10)
    sort_options.current(0)
    sort_options.pack(side=tk.LEFT)
    sort_options.bind("<<ComboboxSelected>>", lambda e: sort_expenses(sort_options.get()))

    budget_btn = tk.Button(top_frame, text="Set Budget", command=set_budget, bg="#4CAF50", fg="white")
    budget_btn.pack(side=tk.LEFT, padx=10)

    budget_label = tk.Label(root, text="Budget limit: Not set", font=("Arial", 12), bg="#f0f0f0")
    budget_label.pack()

    list_frame = tk.Frame(root)
    list_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(
        list_frame,
        width=100,
        height=20,
        yscrollcommand=scrollbar.set,
        font=("Consolas", 11),
        selectbackground="#6ea8fe",
        selectforeground="white",
    )
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    btn_frame = tk.Frame(root, bg="#f0f0f0")
    btn_frame.pack(pady=10)

    btn_style = {
        "font": ("Arial", 12),
        "bg": "#007acc",
        "fg": "white",
        "activebackground": "#005f99",
        "width": 15,
        "bd": 0,
        "relief": tk.RAISED,
    }

    tk.Button(btn_frame, text="Add Expense", command=add_expense_gui, **btn_style).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Edit Selected", command=edit_expense_gui, **btn_style).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Delete Selected", command=delete_expense_gui, **btn_style).grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="Export CSV", command=export_csv_gui, **btn_style).grid(row=0, column=3, padx=5)
    tk.Button(btn_frame, text="Import CSV", command=import_csv_gui, **btn_style).grid(row=0, column=4, padx=5)
    tk.Button(btn_frame, text="Category Pie Chart", command=show_category_pie_chart, **btn_style).grid(row=0, column=5, padx=5)

    refresh_listbox()
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
