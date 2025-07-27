# Disclaimer

This application retrieves financial data from multiple publicly available sources, including Yahoo Finance (via the `yfinance` library) for market prices and ICICI Direct for an initial master list of securities.

By using this application, you acknowledge and agree to the following terms:

*   **For Informational & Non-Commercial Use Only:** All data, including asset prices and details, is provided for personal, informational, and non-commercial use only. It should not be considered professional financial advice.

*   **No Guarantees of Accuracy:** The data sources used are not official, supported APIs. Their availability, accuracy, and timeliness are not guaranteed. The underlying public data may change or become unavailable at any time.

*   **Data May Be Delayed:** To improve performance and reduce reliance on external APIs, this application uses a caching system (Redis). This means that market prices and other financial data may be delayed. Current prices are cached for up to 15 minutes, and historical data may be cached for up to 24 hours.

*   **Not for Trading:** Do not use the data provided by this application to make financial trading decisions. Always consult official sources or a qualified financial advisor.