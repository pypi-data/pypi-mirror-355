from collections import defaultdict
import csv
import json
import Stock

class portfolio:
    # init value of stock
    def __init__(
            self,
            owner,
            stocksList=None,  
            amountByCost=0.0,
            unrealized=0.0,
            unrealizedInPercentage=0.0,
            realized=0.0,
            cashbalance=100000.0,
            prevousDay_maxDD = None,
            nav=0.0,
            max_nav = None,
            min_nav = None,
            max_Draw_down = 0.0,
            No_win = 0,
            No_sell = 0
        ):
        self.owner = owner
        self.stocksList = stocksList if stocksList is not None else []
        self.amountByCost = amountByCost
        self.unrealized = unrealized
        self.unrealizedInPercentage = unrealizedInPercentage
        self.realized = realized
        self.cashbalance = cashbalance
        self.initial_cash = cashbalance
        self.prevousDay_maxDD = prevousDay_maxDD
        self.nav = nav
        self.max_nav = max_nav
        self.min_nav = min_nav
        self.max_Draw_down = max_Draw_down
        self.No_win = No_win
        self.No_sell = No_sell

    # Add new Stock to portfolio
    def add_stock(self, stock):
        self.stocksList.append(stock)
        self.update_portfolio_totals()

    # decrease stock volume, if the volume is reach 0 remove that stock out of the port
    def decrease_stock_volume(self,symbol, volume, price):

        self.stocksList.sort(key=lambda stock: stock.buy_time)

        remaining_volume = volume
        for s in list(self.stocksList):

            if remaining_volume == 0:
                break

            if s.get_symbol() == symbol:
                vol_to_decrease = min(s.get_actual_vol(), remaining_volume)

                if (self.isWin((price * volume),self.cal_avg_cost(symbol))):
                    self.increase_numberOfWin()
                if s.get_actual_vol() >= remaining_volume:
                     # increase number of win if buy price is less than sell price

                    # count number of sell count
                    self.increase_numberOfSell()

                    # decrease volume of stock
                    s.decreaseStockVolume(vol_to_decrease)
                    remaining_volume -= vol_to_decrease
                    
                    # If actual_vol becomes 0 or below, remove this stock
                    if s.get_actual_vol() <= 0:
                        self.stocksList.remove(s)
                else:
                    volume_to_decrease = remaining_volume - s.get_actual_vol()
                    # count number of sell count
                    self.increase_numberOfSell()

                    # decrease volume of stock
                    s.decreaseStockVolume(volume_to_decrease)
                    
                    # If actual_vol becomes 0 or below, remove this stock
                    if s.get_actual_vol() <= 0:
                        self.stocksList.remove(s)


        self.update_portfolio_totals()

    def update_max_min_nav(self):
        nav = self.get_nav()

        if self.max_nav is None or nav > self.max_nav:
            self.max_nav = nav
            self.min_nav = nav  # reset only when new peak is found
        elif nav < self.min_nav:
            self.min_nav = nav  # track lowest point *after* the peak

    def update_sold_stock_valueToPort(self,amount):
        self.cashbalance += amount

    def update_Buy_stock_valueToPort(self,amount):
        self.cashbalance -= amount

    # Calculate Unrealized of the stock
    def calUnrealized(self):
        self.unrealized = self.market_value - self.amount_cost

    # Calculate unrealized In Percentage of the stock
    def calUnrealizedInPercentagee(self):
        self.unrealizedInPercentage = (
            (self.unrealized / self.amount_cost) * 100 if self.amount_cost != 0 else 0.0
        )

    # cal avg cost
    def cal_avg_cost(self, symbol):
        symbol_stocks = self.get_stock_info_by_symbol(symbol)
        total_volume = 0
        total_cost = 0.0
        for stock in symbol_stocks:
            volume = stock.get_actual_vol()
            price = stock.get_buy_price()
            total_volume += volume
            total_cost += price * volume

        if total_volume == 0:
            return 0.0  # Avoid division by zero

        avg_cost = total_cost / total_volume
        return avg_cost

    # cal max DD
    def cal_maxDD(self):
        if self.max_nav and self.min_nav and self.max_nav != 0:
            current_dd = ((self.min_nav - self.max_nav) / self.max_nav) * 100
            self.prevousDay_maxDD = min(self.prevousDay_maxDD or 0, current_dd)
            self.max_Draw_down = self.prevousDay_maxDD

    # cal win rate
    def cal_winRate(self):
        if self.No_sell == 0 or self.No_win == 0:
            return 0
        return (self.No_win / self.No_sell) * 100

    # Calculate cash balance in the port
    def calculate_cash_balance(self):
        total_invested = sum(stock.amount_cost for stock in self.stocksList)
        total_realized = sum(stock.realized for stock in self.stocksList)
        self.cashbalance = self.cashbalance - total_invested + total_realized
        return self.cashbalance
    
    # Calculate NAV (Net Asset Value) of the port
    def calculate_nav(self):
        self.nav = self.get_unrealized() + self.cashbalance

    # Calculate Return on Investment (ROI) as a percentage based on initial cash.
    def calculate_roi(self):
        current_nav = sum(stock.market_value - stock.amount_cost for stock in self.stocksList) + self.cashbalance
        return ((current_nav - self.initial_cash) / self.initial_cash) * 100 if self.initial_cash != 0 else 0.0
    
    #calculate Relative Drawdown
    def cal_relativeDrawdown(self):
        return (self.max_Draw_down/self.initial_cash)/100

    # Update portfolio
    def update_portfolio_totals(self):
        for stock in self.stocksList:
            symbol = stock.get_symbol()
            Symbol_avg_cost = self.cal_avg_cost(symbol)
            stock.calAmount_Cost(Symbol_avg_cost)
            stock.set_avg_cost(Symbol_avg_cost)
            self.unrealized += stock.get_unrealized()
        self.amountByCost = sum(stock.get_amount_cost() for stock in self.stocksList)
        self.unrealized = sum(stock.get_unrealized() for stock in self.stocksList)
        self.realized = sum(stock.get_realized() for stock in self.stocksList)
        self.unrealizedInPercentage = (
            (self.unrealized / self.amountByCost) * 100 if self.amountByCost != 0 else 0.0
        )

    # calculate calmar ratio
    def cal_calmar_ratio(self):
        if self.max_Draw_down == 0:
            return 0
        return self.calculate_roi() / self.max_Draw_down

    # Update all stock market price 
    def update_market_prices(self, price_updates: dict):
        """
        price_updates: dict mapping symbol (str) -> new market price (float)
        """
        for stock in self.stocksList:
            if stock.get_symbol() in price_updates:
                new_price = price_updates[stock.get_symbol()]
                symbol_avg_cost = self.cal_avg_cost(stock.get_symbol())
                stock.updateStockMk_value(new_price,symbol_avg_cost)
        # After updating all stocks, recalc totals

        self.update_portfolio_totals()
        self.calculate_nav()  # or however you calculate current NAV
        self.update_max_min_nav()
        self.cal_maxDD()

        # print(f"[DEBUG] NAV: {self.nav}, Max NAV: {self.max_nav}, Min NAV: {self.min_nav}, Max DD: {self.max_Draw_down}")

    def has_stock(self, symbol, volume):
        total_volume = 0.0
        for stock in self.stocksList:
            if stock.get_symbol() == symbol:
                total_volume += stock.get_actual_vol()
        if total_volume >= volume:
            return True
        return False

    # getter methods
    def get_owner(self):
        return self.owner

    def get_stocks_list(self):
        return self.stocksList

    def get_amount_by_cost(self):
        return self.amountByCost

    def get_unrealized(self):
        return self.unrealized

    def get_unrealized_in_percentage(self):
        return self.unrealizedInPercentage

    def get_realized(self):
        return self.realized

    def get_cash_balance(self):
        return self.cashbalance

    def get_initial_cash(self):
        return self.initial_cash

    def get_prevous_day_max_dd(self):
        return self.prevousDay_maxDD

    def get_nav(self):
        return self.nav

    def get_max_nav(self):
        return self.max_nav

    def get_min_nav(self):
        return self.min_nav

    def get_max_draw_down(self):
        return self.max_Draw_down

    def get_number_of_wins(self):
        return self.No_win

    def get_number_of_sells(self):
        return self.No_sell
    
    def get_all_stocks_info(self):
        """
        Returns a list of aggregated stock info dictionaries by symbol.
        Combines multiple lots of the same stock into a single summary row.
        """
        aggregated = defaultdict(lambda: {
            "Symbol": "",
            "Buy Price": 0.0,
            "Actual Volume": 0,
            "Total Cost": 0.0,
            "Market Value": 0.0,
            "Unrealized P&L": 0.0,
            "Realized P&L": 0.0,
            "Buy_time": "",
            "Market Price": 0.0  # last seen market price
        })

        for stock in self.stocksList:
            info = stock.get_stock_info()
            symbol = info["Symbol"]

            aggregated[symbol]["Symbol"] = symbol
            aggregated[symbol]["Buy Price"] = info["Buy Price"]
            aggregated[symbol]["Actual Volume"] += info["Actual Volume"]
            aggregated[symbol]["Total Cost"] += info["Amount Cost"]
            aggregated[symbol]["Market Value"] += info["Market Value"]
            aggregated[symbol]["Unrealized P&L"] += info["Unrealized P&L"]
            aggregated[symbol]["Realized P&L"] += info["Realized P&L"]
            aggregated[symbol]["Buy_time"] = info["Buy_time"]  # can use most recent or earliest if needed
            aggregated[symbol]["Market Price"] = info["Market Price"]

        result = []
        for sym_data in aggregated.values():
            actual_vol = sym_data["Actual Volume"]
            avg_cost = sym_data["Total Cost"] / actual_vol if actual_vol != 0 else 0.0
            unrealized_pct = (sym_data["Unrealized P&L"] / sym_data["Total Cost"] * 100) if sym_data["Total Cost"] != 0 else 0.0

            result.append({
                "Symbol": sym_data["Symbol"],
                "Buy Price": sym_data["Buy Price"],
                "Actual Volume": actual_vol,
                "Average Cost": avg_cost,
                "Market Price": sym_data["Market Price"],
                "Amount Cost": sym_data["Total Cost"],
                "Market Value": sym_data["Market Value"],
                "Unrealized P&L": sym_data["Unrealized P&L"],
                "Unrealized %": unrealized_pct,
                "Realized P&L": sym_data["Realized P&L"],
                "Buy_time": sym_data["Buy_time"]
            })

        return result
    
    def get_stock_info_by_symbol(self, symbol):
        return [stock for stock in self.stocksList if stock.get_symbol() == symbol]


    # Summary info
    def get_portfolio_info(self):
        return {
            "Owner": self.owner,
            "Number of Stocks": len(self.stocksList),
            "Total Cost": round(self.amountByCost, 2),
            "Unrealized P&L": round(self.unrealized, 2),
            "Unrealized %": round(self.unrealizedInPercentage, 2),
            "Realized P&L": round(self.realized, 2),
            "Cash Balance": round(self.cashbalance, 2),
            "Net Asset Value": round(self.nav, 2),
            "Max NAV": round(self.max_nav, 2) if self.max_nav is not None else None,
            "Min NAV": round(self.min_nav, 2) if self.min_nav is not None else None,
            "Max Drawdown (%)": round(self.max_Draw_down, 2) if self.max_Draw_down is not None else None,
            "Relative Drawdown": self.cal_relativeDrawdown(),
            "Calmar Ratio": self.cal_calmar_ratio(),
            "Previous Day Max DD (%)": round(self.prevousDay_maxDD, 2) if self.prevousDay_maxDD is not None else None,
            "Number of Wins": self.No_win,
            "Number of Sells": self.No_sell,
            "Win Rate": self.cal_winRate(),
            "Return rate": self.calculate_roi()
        }
    
    # get number of stock that bought from each symbol
    def get_All_stock_count_by_symbol(self):
        """
        Returns a dict mapping symbol -> number of buy entries in stocksList.
        Each entry counts as one buy regardless of volume.
        """
        buy_count = defaultdict(int)
        for stock in self.stocksList:
            symbol = stock.get_symbol()
            buy_count[symbol] += 1
        return dict(buy_count)

    def increase_numberOfWin(self):
        self.No_win += 1

    def increase_numberOfSell(self):
        self.No_sell += 1

    def isWin(self,price,avg_cost):
        return price > avg_cost
    
    def export_stocks_to_csv(self):
        stocks = self.get_all_stocks_info()
        if not stocks:
            print("No stock in portfolio")
            return

        keys = ["Symbol","Actual Volume", "Buy Price", "Buy time"]

    def save_to_file(self, filename="portfolio.json"):
        data = {
            "owner": self.owner,
            "cashbalance": self.cashbalance,
            "realized": self.realized,
            "stocksList": [stock.to_dict() for stock in self.stocksList],
            "No_win": self.No_win,
            "No_sell": self.No_sell,
            "prevousDay_maxDD": self.prevousDay_maxDD
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4, default=str)

    @classmethod
    def load_from_file(cls, filename="portfolio.json"):
        with open(filename, "r") as f:
            data = json.load(f)
            stocks_data = data["stocksList"]
            stocksList = [Stock.stock.from_dict(d) for d in stocks_data]
        return cls(
            owner=data["owner"],
            stocksList=stocksList,
            cashbalance=data["cashbalance"],
            realized=data["realized"],
            No_win=data.get("No_win", 0),
            No_sell=data.get("No_sell", 0),
            prevousDay_maxDD=data.get("prevousDay_maxDD", None)
        )
