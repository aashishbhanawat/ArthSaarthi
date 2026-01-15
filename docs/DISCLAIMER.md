# Disclaimer

## Data Sources

This application retrieves financial data from multiple publicly available sources, including:

*   **[NSDL (National Securities Depository Limited)](https://nsdl.co.in/):** For debt instruments master data including bonds, debentures, and government securities.
*   **[BSE (Bombay Stock Exchange)](https://www.bseindia.com/):** For equity bhavcopy, debt bhavcopy, public bond listings, and index summary data.
*   **[NSE (National Stock Exchange)](https://www.nseindia.com/):** For equity bhavcopy and debt/bond listings.
*   **[ICICI Direct](https://www.icicidirect.com/):** For comprehensive security master data (used as fallback source).
*   **[Yahoo Finance](https://finance.yahoo.com/)** (via `yfinance` library): For real-time and historical stock prices.
*   **[AMFI India](https://www.amfiindia.com/):** For the latest Mutual Fund Net Asset Values (NAVs).
*   **[MFAPI](https://mfapi.in/):** For historical Mutual Fund NAV data. *Note: `mfapi.in` is an open-source, unofficial API. While highly reliable, it is not an official AMFI service.*
*   **[Exchange Rate API](https://exchangerate-api.com/):** For foreign exchange rates.

ArthSaarthi is **not affiliated with, endorsed by, or sponsored by** any of these organizations. Data is used for informational purposes only.

---

## Terms of Use

By using this application, you acknowledge and agree to the following terms:

### For Informational & Non-Commercial Use Only

All data, including asset prices, securities information, and portfolio analytics, is provided for **personal, informational, and non-commercial use only**. It should not be considered professional financial advice.

### No Guarantees of Accuracy

The data sources used are publicly available but not official, supported APIs. Their availability, accuracy, and timeliness are **not guaranteed**. The underlying public data may change or become unavailable at any time.

### Data May Be Delayed

To improve performance and reduce reliance on external APIs, this application uses a caching system. This means that:

*   Market prices may be delayed up to **15 minutes**
*   Historical data may be cached for up to **24 hours**
*   Asset master data is refreshed periodically (not real-time)

### Not Investment Advice

**ArthSaarthi is not a registered investment advisor, broker, or financial planner.**

*   Do **not** use the data provided by this application to make financial trading decisions without independent verification.
*   Always consult official exchange sources or a qualified financial advisor for investment decisions.
*   Past performance calculations shown are not indicative of future results.
*   The application calculates metrics like XIRR and Sharpe Ratio for informational purposes only.

### Data Accuracy

*   We strive for accuracy but cannot guarantee all data is correct or current.
*   Users should verify important financial information with official sources.
*   Transaction imports may have errors; always review before committing.
*   Tax calculations and reports are estimates only - consult a tax professional.

### Limitation of Liability

The developers and contributors of ArthSaarthi shall not be held liable for any financial losses, incorrect data, missed opportunities, or any other damages arising from the use of this application.

---

## Privacy

In **Desktop Mode**, all your financial data is stored locally on your device in an encrypted SQLite database. No data is transmitted to external servers except for:

1. Asset price and market data requests to the sources listed above
2. Foreign exchange rate lookups for multi-currency support

In **Server Mode**, data is stored in your self-hosted PostgreSQL database. You control all your data.

ArthSaarthi does not collect, store, or transmit any user data to the application developers.

---

## Open Source

ArthSaarthi is open-source software licensed under the MIT License. You are free to review, modify, and distribute the code according to the license terms.

---

*Last updated: December 2025*