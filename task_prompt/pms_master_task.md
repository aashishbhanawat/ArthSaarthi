## Master Orchestration Prompt 🧑‍🎤

**Goal:** To orchestrate the entire development lifecycle of **ArthSaarthi**, a personal portfolio management web application, guiding various AI roles through requirement gathering, design, development (feature by feature), and deployment, ensuring comprehensive documentation and adherence to Agile principles.

**Instructions:**
"We are developing **ArthSaarthi**, a web-based personal portfolio management application. We will follow an Agile SDLC, developing features iteratively. Your task is to act as the **Master Orchestrator**. You will invoke specific AI roles and guide them through each stage: **Requirement Analyst, Solution Architect, UI/UX Designer, Backend Developer, Frontend Developer, Database Administrator, DevOps Engineer, and QA Engineer**.

For each stage, you will:
1.  **Announce the current stage and the AI role(s) involved.**
2.  **Provide the specific prompt for that role.**
3.  **Collect and synthesize the output from the AI role.**
4.  **Present potential approaches, pros, and cons for key decisions.**
5.  **Summarize the agreed-upon plan, including file changes, API updates, and database schema changes.**
6.  **Ask for my confirmation before proceeding to the next step.**
Our application, **ArthSaarthi**, will be deployed in a Docker environment or as an independent app. We will use Gemini-CLI or other GenAI for code generation.

Let's begin with **Stage 1: Requirement Gathering** and invoke the **Requirement Analyst**."

---

## 1. Requirement Gathering (Stage 1) 📋

**Role:** Requirement Analyst 🕵️‍♀️

**Objective:** To gather and document a comprehensive list of functional and non-functional requirements for the personal portfolio management web application.

### Prompt for Requirement Analyst

"You are the **Requirement Analyst**. Your task is to elicit a detailed list of features for **ArthSaarthi**, a web-based personal portfolio management application. Consider the core functionalities a user would expect for managing their personal investments (stocks, bonds, crypto, mutual funds, real estate, etc.), tracking performance, and making informed decisions. Also, consider non-functional requirements like security, performance, scalability, and usability.

**Please provide:**
1.  A categorized list of **functional requirements** (e.g., User Authentication, Portfolio Tracking, Transaction Management, Reporting, etc.).
2.  A list of **non-functional requirements** (e.g., Security, Performance, Usability, Scalability, Maintainability, Deployment).
3.  Any **clarifying questions** you have about the scope or specific features.

Think about what a user needs from an end-to-end perspective for personal finance management."

---

## 2. Architecture & Design (Stage 2) 🏗️

**Role:** Solution Architect 🌐

**Objective:** To design the high-level architecture, propose technologies, and outline the system flow based on the gathered requirements.

### Prompt for Solution Architect

"You are the **Solution Architect**. Based on the functional and non-functional requirements provided by the Requirement Analyst, propose a high-level architecture for **ArthSaarthi**. The application should be web-based and deployable via Docker or as an independent app.

**Consider and detail the following:**
1.  **Overall Architecture Pattern:** (e.g., Monolithic, Microservices, Client-Server). Provide pros and cons for each and recommend one.
2.  **Technology Stack (Backend, Frontend, Database):**
    * **Backend Framework(s):** (e.g., Node.js with Express, Python with Django/Flask, Spring Boot with Java, Ruby on Rails). Discuss pros and cons, and recommend one.
    * **Frontend Framework(s):** (e.g., React, Angular, Vue.js). Discuss pros and cons, and recommend one.
    * **Database System(s):** (e.g., PostgreSQL, MySQL, MongoDB, SQLite). Discuss pros and cons, and recommend one, considering data integrity for financial data.
3.  **Deployment Strategy:** (Docker, direct deployment). Explain how Docker would be used (e.g., containerizing frontend, backend, database).
4.  **High-Level Data Flow:** Describe how data will move between the frontend, backend, and database for a key operation (e.g., adding a new stock transaction).
5.  **Mock UI/Wireframe Ideas:** Describe key screens and their interactions. (The UI/UX Designer will create detailed mockups later).

**Provide potential approaches for each decision with their respective pros and cons.**"

---

## 3. UI/UX Design (Stage 3) 🎨

**Role:** UI/UX Designer 🖥️

**Objective:** To create mockups and wireframes for the user interface, ensuring a user-friendly and intuitive experience.

### Prompt for UI/UX Designer

"You are the **UI/UX Designer**. Based on the functional requirements from the Requirement Analyst and the architectural overview from the Solution Architect, create detailed mockups and wireframes for the key screens of **ArthSaarthi**. Focus on a clear, intuitive, and efficient user experience.

**For each key feature/screen (e.g., Dashboard, Add Investment, Transaction List, Performance Report, User Profile), provide:**
1.  **Wireframe/Mockup Description:** Describe the layout, key elements, and user interactions. (Use text-based descriptions, or suggest a simple ASCII art representation if possible.)
2.  **User Flow:** Explain the typical path a user would take to complete a task (e.g., from login to viewing portfolio performance).
3.  **Design Considerations:** Justify your design choices with considerations for usability, accessibility, and responsiveness. Explain your choices regarding navigation, data visualization, input forms, and overall aesthetic (e.g., clean, professional).
4.  **Key UI Components:** List necessary components (buttons, input fields, charts, tables).

**Example Screens to consider:**
* **Login/Registration**
* **Dashboard:** Overview of portfolio value, recent transactions, quick insights.
* **Add Investment:** Form for adding new stock, crypto, mutual fund, etc.
* **Portfolio Details:** List of holdings, current prices, profit/loss.
* **Transaction History:** List of all buys/sells.
* **Performance Reports:** Charts and tables for historical performance.
* **Settings/User Profile**"

---

## 4. Module Development (Stage 4 - Iterative: Feature by Feature) 🚀

This stage will be repeated for each module/feature identified in the requirements. The Master Orchestrator will decide which module to develop next based on the Agile backlog.

**Roles involved in each iteration:** Backend Developer, Frontend Developer, Database Administrator, QA Engineer, DevOps Engineer.

### Master Orchestration Prompt for Module Development

"We are now entering **Stage 4: Module Development**. We will develop features one by one in an Agile manner. I will specify the feature, and you will invoke the relevant AI roles to plan, implement, and test it.

For each feature, we'll follow these steps:
1.  **Feature Definition & Context Scaffolding:**
    *   Define the current feature to be developed.
    *   Request a full project file listing (`ls -R`) to build an accurate context map and prevent code duplication.
2.  **Backend Development Planning (Backend Developer & Database Administrator):**
    * API Endpoints (new/updated)
    * Database Schema Changes (new tables, columns, relationships)
    * Proposed Backend Files/Folders
3.  **Frontend Development Planning (Frontend Developer & UI/UX Designer):**
    * UI Components
    * Proposed Frontend Files/Folders
    * User Interactions
4.  **Code Generation Request:** Once plans are confirmed, request the AI to generate the code.
5.  **Testing & Debugging Workflow (QA Engineer & All Roles):**
    *   **Testing Plan:** The QA Engineer will define unit tests, integration tests, and acceptance criteria.
    *   **E2E Test Plan:** The QA Engineer will also define a high-level E2E test case to be added for the feature.
    *   **Rigorous RCA:** When an error occurs, the AI must analyze the **full stack trace**, validate dependencies by requesting to see imported files, and state its hypothesis before proposing a fix.
    *   **Local Testing Environment:** For development and testing in a non-Dockerized environment, refer to the instructions in `task_prompt/AGENTS.md`. This guide details how to use the `run_local_tests.sh` script to execute the full test suite.
    *   **Formal Bug Triage:** Before filing a new bug, the AI must search the temporary bug log (`docs/bug_report_temp.md`) for existing issues. It will propose updating an existing bug before creating a new one. The main `docs/bug_reports.md` file is for historical context only.
    *   **No Debugging Loops:** If a proposed fix does not work, the AI must not suggest the same fix again. It must re-evaluate its hypothesis, ask for more information (e.g., different logs, file contents), and propose a new, distinct path forward.

6.  **Deployment/Environment Updates (DevOps Engineer):**
    *   A plan for database schema initialization (e.g., `create_all` for dev, migrations for prod).
    *   Docker/Deployment Script Updates
    *   Environment Variables
7.  **Code Generation Workflow:**
    *   **To prevent truncated responses for large, multi-file changes, first provide a list of all files that need to be created or modified.**
    *   **Then, ask the user which file they would like to see the changes for first.**
    *   **Proceed with generating the code for one file at a time, as directed by the user.**
7.  **Review and Iteration.**
8.  **Documentation & Commit Workflow:**
    *   Append a detailed entry to `docs/workflow_history.md` summarizing the task, key prompts used, a summary of the AI's output, a comprehensive list of file changes, verification steps, and the final outcome.
    *   Systematically update all other relevant project documents as per the checklist in `docs/COMMIT_TEMPLATE.md`.
    *   Generate a final, standardized commit message using the format specified in `task_prompt/COMMIT_TEMPLATE.md`.

**A `.gitignore` file should be created early in the process to exclude virtual environments, `.env` files, and `__pycache__` directories.**


You are now ready to start development of new module.

**All planned MVP features are now complete, stable, and covered by a foundational E2E test suite. "Real Data Integration (FR5)" was completed in a previous release.**

The next priority is to complete the **Automated Data Import (FR7)** feature. The backend for this feature is partially implemented but contains stubs.

Before we proceed with development, we will first run all test suites (backend, frontend, E2E) to ensure there has been no regression. After confirming the stability of the application, we will begin completing the backend implementation for FR7.

Now, let's proceed with the full test suite execution.

#### 4.1. Backend Development Planning (for a specific Feature) 💻🗄️

**Roles:** Backend Developer & Database Administrator

**Objective:** To design the backend logic, APIs, and database schema for the current feature.

### Prompt for Backend Developer & Database Administrator

"You are the **Backend Developer** and **Database Administrator**. The current feature to develop is **User Authentication (Registration and Login)**.

**As Backend Developer, propose:**
1.  **New/Updated API Endpoints:**
    *   Ensure all directories under `app/` have an `__init__.py` file.
    *   Use absolute imports within the application (e.g., `from app.core import security`).
    *   Ensure all dependencies (like `email-validator`, `python-multipart`) are added to `requirements.txt`.
    * `POST /api/register` (for user registration)
    * `POST /api/login` (for user login)
    * `GET /api/user/profile` (for fetching user details after authentication - *optional for initial sprint, but good to think about*)
2.  **Request/Response Schemas** for these APIs (e.g., JSON structure).
3.  **Backend Logic Overview:** Describe the steps involved in handling registration (hashing passwords, saving to DB) and login (verifying credentials, generating tokens).
4.  **Proposed Backend Files/Folders:** List the new files and their purpose (e.g., `routes/auth.js`, `controllers/authController.js`, `models/User.js`).
5.  **Potential Implementation Approaches for Authentication:** Discuss pros and cons, and recommend one (e.g., JWT, Session-based).

**As Database Administrator, propose:**
1.  **Database Schema Changes:** Define the `users` table, including columns (e.g., `id`, `username`, `email`, `password_hash`, `created_at`). Specify data types and constraints.
2.  **Rationale** for the chosen schema.

**Provide complete details for these plans, including any specific libraries or concepts you'd use.**"

#### 4.2. Frontend Development Planning (for a specific Feature) 🖥️🎨

**Roles:** Frontend Developer & UI/UX Designer

**Objective:** To design the frontend components and user interactions for the current feature, integrating with the planned backend APIs.

### Prompt for Frontend Developer & UI/UX Designer

"You are the **Frontend Developer** and **UI/UX Designer**. The current feature to develop is **User Authentication (Registration and Login)**. The Backend Developer has provided the API specifications.

**As Frontend Developer, propose:**
1.  **UI Components:** List the specific components needed (e.g., input fields for username/email/password, login button, register button, validation messages).
2.  **Proposed Frontend Files/Folders:** List the new files and their purpose (e.g., `src/pages/AuthPage.js`, `src/components/LoginForm.js`, `src/components/RegisterForm.js`).
3.  **User Interactions:** Describe the flow on the client side (e.g., user enters credentials, clicks button, success/error message displayed, redirection upon successful login).
4.  **Integration with Backend:** How will the frontend consume the backend APIs? (e.g., using `fetch` or Axios).
5.  **State Management:** How will authentication state be managed in the frontend? (e.g., React Context, Redux, local state).

**As UI/UX Designer, refine:**
1.  **Wireframe/Mockup Refinement:** Provide a more detailed description or ASCII art of the Login and Registration forms, focusing on user experience, error handling display, and visual feedback.
2.  **Accessibility Considerations:** Briefly mention any accessibility features to include.


#### 4.3. Code Generation Request (for a specific Feature) 🤖

**Role:** Master Orchestrator (to Gemini-CLI/GenAI)

**Objective:** To instruct the AI code generation tool to write the code based on the approved plans.

### Prompt for Code Generation

"**Master Orchestrator to Gemini-CLI/GenAI:**

"Based on the approved Backend Development Plan (API endpoints, logic, database schema) and Frontend Development Plan (UI components, interactions) for the **User Authentication (Registration and Login)** feature, generate the necessary code.

**Backend (Python with Flask/Django, Node.js with Express - *select one based on Solution Architect's recommendation*):**
* Create files for:
    * User Model/Schema
    * Authentication Routes
    * Authentication Controller/Logic
* Implement:
    * User registration with password hashing.
    * User login with credential verification and JWT token generation/session management.
    * Database interaction (create user, find user).

**Frontend (React/Angular/Vue.js - *select one based on Solution Architect's recommendation*):**
* Create files for:
    * Login Component
    * Registration Component
    * Authentication Page (to house both forms)
* Implement:
    * Forms with input fields and submission logic.
    * Client-side validation.
    * API calls to the backend.
    * Handling success/error responses (e.g., showing messages, redirecting).
    * Basic state management for authentication.

**Database (SQL schema - if applicable):**
* Provide the SQL DDL for the `users` table.
Please implement the test and documentation steps too.

**Ensure the code is modular, follows best practices, and includes comments where necessary.**"

#### 4.4. Testing Plan (for a specific Feature) 🔎

**Role:** QA Engineer

**Objective:** To define the test cases and acceptance criteria for the developed feature.

### Prompt for QA Engineer

"You are the **QA Engineer**. The **User Authentication (Registration and Login)** feature has just been developed.

**Your task is to create a comprehensive testing plan, including:**
1.  **Unit Tests:** List specific functions/methods in the backend and frontend that need unit testing, and describe what each test should verify (e.g., password hashing correctness, form validation logic).
2.  **Integration Tests:** Outline tests that verify the interaction between frontend and backend, and backend and database (e.g., successful registration followed by successful login, invalid login attempts).
3.  **Acceptance Criteria (User Stories):** For both registration and login, define clear, testable criteria from a user's perspective (e.g., 'As a new user, I can successfully register with a unique email and password and be redirected to the dashboard.').
4.  **Edge Cases/Negative Testing:** Identify scenarios to test for robustness (e.g., empty fields, existing email during registration, incorrect credentials during login, password strength).
5.  **Security Testing:** Suggest basic security tests (e.g., SQL injection attempts on login fields, XSS in error messages).

**Provide these in a clear, actionable format.**"

#### 4.5. Deployment/Environment Updates (for a specific Feature) ⚙️

**Role:** DevOps Engineer

**Objective:** To plan for the deployment aspects of the new feature, especially concerning Docker and environment setup.

### Prompt for DevOps Engineer

"You are the **DevOps Engineer**. The **User Authentication (Registration and Login)** feature has been developed and tested.

**Your task is to outline the necessary updates for deployment, assuming a Dockerized environment:**
1.  **Dockerfile Updates:** Any changes needed in the `Dockerfile` for the backend or frontend (e.g., new dependencies, changes in build process).
2.  **Docker Compose Updates:** If using `docker-compose`, any new services, volumes, or network configurations needed (e.g., adding a database service, linking services).
3.  **Environment Variables:** List any new environment variables required for the feature (e.g., `JWT_SECRET_KEY`, database connection strings).
4.  **Environment File Handling:** Specify that `docker-compose.yml` should use the `env_file` directive to load variables from a `.env` file, which should be listed in `.gitignore`.
5.  **Database Initialization:** Outline the strategy for creating the database schema (e.g., using SQLAlchemy's `create_all` for development).
6.  **CORS Policy:** Note if any changes to the backend's CORS policy are required.
7.  **Monitoring Considerations:** What metrics or logs should be monitored for this feature (e.g., failed login attempts, new user registrations)?

**Provide these details clearly, assuming a standard Docker setup.**"

---

## 5. Deployment (Stage 5 - Final) 🚀

**Roles:** DevOps Engineer & Master Orchestrator

**Objective:** To finalize the deployment process for the complete application.

### Prompt for DevOps Engineer (Final Deployment)

"You are the **DevOps Engineer**. All features and modules for the personal portfolio management application are now complete, integrated, and tested.

**Your task is to provide a comprehensive final deployment plan, considering a Dockerized environment:**
1.  **Final Dockerfile(s):** Provide the complete `Dockerfile` for the backend and frontend, assuming a production build.
2.  **Final Docker Compose File:** Provide the `docker-compose.yml` file that orchestrates the backend, frontend, and database services. Include considerations for persistent data (volumes), networking, and environment variables.
3.  **Deployment Script/Commands:** Outline the exact commands to build and run the entire application using Docker (e.g., `docker-compose build`, `docker-compose up -d`).
4.  **Production Readiness Checklist:** List essential steps for production deployment (e.g., securing environment variables, setting up SSL/TLS, backup strategy, logging, monitoring, error alerting).
5.  **Scalability Considerations:** Briefly discuss how the Docker setup facilitates scaling (e.g., running multiple instances of backend containers).
6.  **Troubleshooting Tips:** Common issues during deployment and how to debug them.

**Ensure all necessary configurations for a production environment are considered.**"