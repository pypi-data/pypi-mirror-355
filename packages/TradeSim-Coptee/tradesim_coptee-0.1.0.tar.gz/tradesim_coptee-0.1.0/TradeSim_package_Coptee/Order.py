import time
import csv
import importlib.resources

class order:
    _order_counter = 1
    _set50_symbols = set()
    _csv_loaded = False

    @classmethod
    def load_set50_symbols(cls):
        if cls._csv_loaded:
            return
        try:
            with importlib.resources.open_text("TradeSim_package_Coptee", "Symbol_SET50.csv", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                headers = [h.strip() for h in reader.fieldnames]

                # Find symbol column
                symbol_col = next((h for h in headers if h.lower() == "symbol"), None)
                if symbol_col is None:
                    raise KeyError("[ERROR] 'Symbol' column not found in CSV headers.")

                for row in reader:
                    symbol = row[symbol_col].strip().upper()
                    cls._set50_symbols.add(symbol)

                cls._csv_loaded = True
                print(f"[INFO] Loaded {len(cls._set50_symbols)} SET50 symbols.")
        except FileNotFoundError:
            raise FileNotFoundError("[ERROR] Could not find Symbol_SET50.csv inside the package.")

    # init value to order
    def __init__(
        self,
        ownerPortfolio: 'portfolio',
        volume: float,
        price: float,
        side: str,
        symbol: str,
        timestamp: float = None
        ):
        order.load_set50_symbols()  # Ensure SET50 is loaded
        if not self.validate_order(volume, side, symbol):
            raise ValueError("Invalid order parameters: volume or side is incorrect")
        self.order_number = f"ORD{order._order_counter:05d}"  # e.g., ORD00001
        order._order_counter += 1  # Increment for next order

        self.ownerPortfolio = ownerPortfolio
        self.volume = volume
        self.price = price
        self.side = side
        self.symbol = symbol
        self.timestamp = timestamp if timestamp is not None else time.time()
        
    @classmethod
    def validate_order(cls, volume, side, symbol):
        errors = []
        if (volume % 100.0) != 0:
            errors.append("Volume must be a multiple of 100.")
        if side.capitalize() not in {"Buy", "Sell"}:
            errors.append("Side must be 'Buy' or 'Sell'.")
        if symbol.upper() not in cls._set50_symbols:
            errors.append(f"Symbol '{symbol}' is not in SET50.")
        if errors:
            raise ValueError("Invalid order: " + " | ".join(errors))
        return True
        

    # --------- Getter Methods ---------
    def get_order_number(self):
        return self.order_number

    def get_ownerPortfolio(self):
        return self.ownerPortfolio

    def get_volume(self):
        return self.volume

    def get_price(self):
        return self.price

    def get_side(self):
        return self.side

    def get_symbol(self):
        return self.symbol

    def get_timestamp(self):
        return self.timestamp

    def get_formatted_timestamp(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))

    def get_order_info(self):
        return {
            "Order Number": self.get_order_number(),
            "owner": self.ownerPortfolio.get_owner(),
            "Volume": self.get_volume(),
            "Price": self.get_price(),
            "Side": self.get_side(),
            "Symbol": self.get_symbol(),
            "Timestamp": self.get_formatted_timestamp()
        }

    # --------- Setter Methods ---------
    def set_owner(self, owner):
        self.owner = owner

    def set_volume(self, volume):
        self.volume = volume

    def set_price(self, price):
        self.price = price

    def set_side(self, side):
        self.side = side

    def set_symbol(self, symbol):
        self.symbol = symbol