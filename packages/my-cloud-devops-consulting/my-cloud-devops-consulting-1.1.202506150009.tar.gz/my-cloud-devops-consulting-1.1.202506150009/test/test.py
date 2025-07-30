name = input("What is your name? ")
weekly_income = int(input("What is your weekly income? "))
spend_on_food = int(input("Spend on food? "))
spend_on_transportation = int(input("Spend on transportation? "))
spend_on_entertainment = int(input("Spend on entertainment? "))

total_expenses = spend_on_food + spend_on_transportation + spend_on_entertainment
balance_summary = weekly_income - total_expenses
print(f"\nHi {name}! Here's your weekly budget breakdown:")
print(f"Total Income: ${weekly_income}")
print(f"Total Expenses: ${total_expenses}")
print(f"Remaining Savings: ${balance_summary}")