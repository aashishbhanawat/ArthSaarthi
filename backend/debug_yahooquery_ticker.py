from yahooquery import Ticker
import json

def test_ticker(symbol):
    print(f"Testing ticker: {symbol}")
    t = Ticker(symbol)
    modules = t.all_modules
    print("Keys in all_modules:", list(modules.keys()))
    
    if symbol in modules:
        data = modules[symbol]
        print(f"Type of modules[{symbol}]: {type(data)}")
        if isinstance(data, str):
            print(f"Error message: {data}")
        else:
            print(f"Keys in data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    else:
        print(f"Symbol {symbol} NOT found in all_modules keys.")

if __name__ == "__main__":
    test_ticker("NTPC.BO")
    test_ticker("NTPC.NS")
