Based on an analysis of the codebase and the architecture documentation, ArthSaarthi utilizes a few distinct design patterns to keep the application modular, scalable, and maintainable.

Here is a breakdown of the primary design patterns used:

1. N-Tier Layered Architecture (Controller-Service-Repository)
The overarching architectural pattern organizes the backend into distinct layers, ensuring a strict separation of concerns. This is a very common and robust pattern for modern REST APIs.

API / Controller Layer (app/api/v1/endpoints/): These files (like transactions.py or portfolios.py) act as the entry point. They handle HTTP requests, validate input using Pydantic, and return HTTP responses. They contain almost no business logic.
Service Layer (app/services/): This layer houses the complex business logic. Examples include 

capital_gains_service.py
, 

benchmark_service.py
, and 

schedule_fa_service.py
. It bridges the gap between the API and the database.
Data Access / Repository Layer (app/crud/): The crud_*.py files encapsulate all SQLAlchemy database interactions. Any code needing to read or write to the database goes through these files, abstracting away the SQL syntax from the rest of the app.
2. Strategy Pattern
The Strategy Pattern is used to define a family of algorithms, encapsulate each one, and make them interchangeable at runtime.

Where it's used (app/services/providers/): The FinancialDataService uses this pattern heavily. Instead of a massive if/else block to figure out how to fetch prices, the system dynamically selects the appropriate "Provider Data Strategy" (e.g., AmfiProvider for mutual funds, NseProvider or BseProvider for Indian equities, and YfinanceProvider as a fallback or for international assets) depending on the context.
3. Factory Method Pattern
The Factory Pattern provides an interface for creating objects in a superclass, but allows subclasses to alter the type of objects that will be created.

Where it's used (

app/services/import_parsers/parser_factory.py
): The application supports automating data imports from dozens of different brokers and banks. The 

get_parser(source_type: str)
 function acts as a factory. When a user uploads a file and selects "Zerodha" or "HDFC Bank FD", the Factory instantiates and returns the exact parser class needed (ZerodhaParser or HdfcFdParser) without the main upload endpoint needing to know the specific implementation details of every parser.
4. Dependency Injection (DI)
Dependency Injection is a technique where an object receives other objects that it depends on, rather than creating them itself.

Where it's used (FastAPI Depends): This is built deeply into FastAPI and used throughout the application's endpoints. Database sessions (get_db), the authenticated user session (get_current_active_user), and even connections to the Redis caching layer are "injected" into the API routes. This makes the code exceptionally easy to unit test using mocked dependencies.