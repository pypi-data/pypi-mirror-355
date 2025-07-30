import Stock
import TransactionLog
import PortSummarize as ps
import pandas as pd
import os


class execution:
    tranLog = TransactionLog.Transaction()
    PortSummarize = ps.summarize
    comm = 0.00157 # commission 0.157%
    vat = 0.07 
    slippage = 0.005 # Slippage

    def __init__(
            self,
            orders_book = None
            ):
            self.Orders_Book = orders_book if orders_book is not None else []

    # add order to order and waiting for matching
    def addOrderToOrders_Book(self,order,row):
        if (order.get_volume() <= row['Volume']):
            self.Orders_Book.append(order)
        else:
            return "Not enough market volume to fulfill the order."

    def isMatch(self, row):

        if len(self.Orders_Book) == 0:
            return "No order in Order book"

        for order in self.Orders_Book:

            try:
                order_time = pd.to_datetime(order.get_timestamp(), unit='s')  # convert float to Timestamp
                matched = True  # Assume match and disprove below

                # print(f"\n🔍 Checking Order: {order.get_order_info()}")

                if row['ShareCode'] != order.get_symbol():
                    # print("❌ Not matched: ShareCode is different.")
                    matched = False

                if row['TradeDateTime'] < order_time:
                    # print(f"❌ Not matched: TradeDateTime {row['TradeDateTime']} is earlier than order time {order_time}.")
                    matched = False

                if order.get_side() == 'Buy' and row['LastPrice'] > order.get_price():
                    matched = False  # Too expensive
                if order.get_side() == 'Sell' and row['LastPrice'] < order.get_price():
                    matched = False  # Too cheap


                if row['Volume'] < order.get_volume():
                    # print(f"❌ Not matched: Volume {row['Volume']} < order volume {order.get_volume()}.")
                    matched = False
                
                if matched:
                    # print(f"✅ Order matched: {order.get_order_info()}")
                    if order.get_side() == 'Buy':
                        if self.verify_transaction(order.get_volume(), order.get_price(),order.get_ownerPortfolio().get_cash_balance()):
                            # calculate vat anc commisstion when buying
                            Buy_value = self.cal_commissionAndVat(order.get_volume(), order.get_price())
                            # create new stock 
                            new_stock = Stock.stock(order.get_symbol(), order.get_volume(), Buy_value , order.get_price(), order.get_timestamp())
                            # add stock to owner portfolio
                            order.get_ownerPortfolio().add_stock(new_stock)
                            # decrease 
                            order.get_ownerPortfolio().update_Buy_stock_valueToPort(self.cal_All_Volume_commissionAndVat(order.get_volume(), order.get_price()))
                            # add order to transaction log
                            self.tranLog.create_transaction_log(order)

                            self.removeOrder(order)
                            continue
                        else:
                            # Fail to verify transaction
                            self.removeOrder(order)
                            continue
                    if order.get_side() == 'Sell':
                        if order.get_ownerPortfolio().has_stock(order.get_symbol(), order.get_volume()):
                            # calculate total value gain from selling
                            sold_value = (order.get_volume() * order.get_price())
                            # deduct with comm and vat
                            comm_amount = sold_value * self.comm
                            vat = comm_amount * self.vat
                            result = (sold_value) - vat - comm_amount - (sold_value * self.slippage)
                            order.get_ownerPortfolio().decrease_stock_volume(order.get_symbol(),order.get_volume(),order.get_price())
                            order.get_ownerPortfolio().update_sold_stock_valueToPort(result)
                            self.tranLog.create_transaction_log(order)
                            self.removeOrder(order)
                        else:
                            # Not enough stock to sell
                            self.removeOrder(order)
                            continue
                    
            except Exception as e:
                print(f"[ERROR] Unexpected error while checking order {order.get_order_number()}: {e}")

    
    def removeOrder(self,order):
        self.Orders_Book.remove(order)

    def getOrderbooksSize(self):
        return len(self.Orders_Book)
    
    def isOrderbooksEmpty(self):
        return self.getOrderbooksSize() == 0

    def verify_transaction(self,volume,price,cashBalance):
        return cashBalance >= (self.cal_All_Volume_commissionAndVat(volume,price)) 
    
    def cal_All_Volume_commissionAndVat(self,volume,price):
        match_price = price + (price * self.slippage)
        amount = match_price * volume
        comm_amount = amount * self.comm
        vat = comm_amount * self.vat
        return amount + comm_amount + vat
    
    def cal_commissionAndVat(self,volume,price):
        match_price = price + (price * self.slippage)
        amount = match_price * volume
        comm_amount = amount * self.comm
        vat = comm_amount * self.vat
        return (amount + comm_amount + vat) / volume
    