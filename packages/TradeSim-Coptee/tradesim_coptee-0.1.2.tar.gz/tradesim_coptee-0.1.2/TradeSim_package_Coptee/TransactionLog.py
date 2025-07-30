import csv
import os

class Transaction:
    def __init__(self, transaction_log=None, csv_file='transaction_log.csv'):
        self.transaction_log = transaction_log if transaction_log is not None else []
        self.csv_file = csv_file

        # Create file with headers if not exists
        if not os.path.isfile(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=[
                    'Order Number', 'owner', 'Volume', 'Price', 'Side', 'Symbol', 'Timestamp'
                ])
                writer.writeheader()

    def create_transaction_log(self, order):
        order_info = order.get_order_info()  # Get dict from order object
        self.transaction_log.append(order_info)

        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'Order Number', 'owner', 'Volume', 'Price', 'Side', 'Symbol', 'Timestamp'
            ])
            writer.writerow(order_info)