# Personal Portfolio Management System (PMS)

This project is a web-based application designed to help users manage their personal investment portfolios. It allows tracking of various assets like stocks, cryptocurrencies, and ETFs, providing performance insights and analytics.

This project is being developed with the guidance of an AI Master Orchestrator, following an Agile SDLC.

## Technology Stack

The proposed technology stack for this project is:

-   **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/)
-   **Frontend:** JavaScript with [React](https://reactjs.org/)
-   **Database:** [PostgreSQL](https://www.postgresql.org/)
-   **Deployment:** [Docker](https://www.docker.com/)

## Project Structure

The project is organized into the following main directories:

-   `/app`: Contains the backend FastAPI application source code.
-   `/frontend`: Contains the frontend React application source code.
-   `/docs`: Contains project documentation, including requirements and architecture designs.

## Running the Project

This project is designed to be run with Docker and Docker Compose for a streamlined development experience.

1.  **Backend Environment:** In the `backend/` directory, create a file named `.env`. You can copy `backend/.env.example` if it exists. Fill in the required values for the database, JWT secret, and CORS origins.

2.  **Frontend Environment:** In the `frontend/` directory, create a file named `.env`. You can copy `frontend/.env.example`. Ensure `VITE_API_BASE_URL` points to the correct backend address (e.g., `http://localhost:8000/api/v1`).

3.  **Build and Run Containers:** From the root directory of the project (`pms_new/`), run:
    ```bash
    docker-compose up --build
    ```

4.  **Accessing the Services:**
    *   The **Backend API** will be available at `http://localhost:8000`.
    *   The interactive API documentation (Swagger UI) is at `http://localhost:8000/docs`.
    *   The **Frontend Application** will be available at `http://localhost:3000`.

## Contributing

Please read CONTRIBUTING.md for details on our development process and the roles involved in this project.

See `docs/troubleshooting.md` for solutions to common setup issues.