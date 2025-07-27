# Code Flow & Contribution Guide

This document provides a deep dive into the application's code structure and data flow. It's designed to help new contributors understand how the frontend and backend work together to deliver a feature.

We will trace a key user story: **Adding a new transaction to a portfolio.**

---

## 1. Frontend Flow: Adding a Transaction

The user journey starts on the `PortfolioDetailPage`, where they click the "Add Transaction" button.

### Step 1: Opening the Modal (`PortfolioDetailPage.tsx`)

The page uses a simple `useState` hook to manage the visibility of the `AddTransactionModal`.

```typescriptreact
// frontend/src/pages/Portfolio/PortfolioDetailPage.tsx

const [isModalOpen, setModalOpen] = useState(false);

// ... later in the JSX
<button onClick={() => setModalOpen(true)} className="btn btn-primary">
    Add Transaction
</button>

{isModalOpen && (
    <AddTransactionModal
        onClose={() => setModalOpen(false)}
        portfolioId={portfolioId}
    />
)}
```

*   **Key Takeaway:** State for UI elements like modals is managed locally within the parent component.

### Step 2: Handling the Form (`AddTransactionModal.tsx`)

This component is responsible for user input, asset searching, and submitting the final data.

1.  **Form Management:** It uses `react-hook-form` for efficient form state management and validation.
2.  **Asset Search:** As the user types in the "Ticker" field, a debounced search is performed using the `lookupAsset` function from `portfolioApi.ts`.
3.  **Mutation with React Query:** When the form is submitted, it calls the `mutate` function from the `useCreateTransaction` custom hook (`usePortfolios.ts`). This hook wraps the actual API call.

```typescriptreact
// frontend/src/components/Portfolio/AddTransactionModal.tsx

const { mutate: createTransaction, isPending, error: apiError } = useCreateTransaction();

const onSubmit = (data: any) => {
    // ... data transformation logic
    createTransaction({ portfolioId, data: transactionData });
};
```

### Step 3: The API Service Layer (`portfolioApi.ts` & `usePortfolios.ts`)

*   `usePortfolios.ts`: This file defines all React Query hooks related to portfolios. The `useCreateTransaction` hook uses the `useMutation` hook from React Query to handle the API call's loading, error, and success states. It also handles cache invalidation on success.
*   `portfolioApi.ts`: This file contains the raw API call logic using an `apiClient` (an Axios instance). The `createTransaction` function here makes the actual `POST` request to the backend.

```typescript
// frontend/src/hooks/usePortfolios.ts
export const useCreateTransaction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ portfolioId, data }: { portfolioId: number; data: TransactionCreate }) =>
      portfolioApi.createTransaction(portfolioId, data),
    onSuccess: () => {
      // Invalidate caches to refetch data
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });
};
```

---

## 2. Backend Flow: Creating a Transaction

The frontend's `POST` request to `/api/v1/portfolios/{portfolio_id}/transactions/` is handled by the FastAPI backend.

### Step 1: Routing & Dependencies (`endpoints/portfolios.py` & `endpoints/transactions.py`)

1.  The request first hits the router defined in `portfolios.py`, which includes the router from `transactions.py`.
2.  FastAPI uses its dependency injection system (`Depends`) to get the `current_user` from the JWT token and the `db` session.

### Step 2: Schema Validation (`schemas/transaction.py`)

The incoming JSON payload is automatically parsed and validated against the `TransactionCreate` Pydantic schema. If any fields are missing or have the wrong data type, FastAPI returns a `422 Unprocessable Entity` error immediately.

### Step 3: Business Logic (`crud/crud_transaction.py`)

The endpoint calls the `create_with_portfolio` method in the CRUD layer. This is where the core business logic resides.

1.  **Validation:** It first checks if the user owns the specified portfolio.
2.  **Validation:** It then performs critical business logic, such as checking if the user has sufficient holdings to make a `SELL` transaction.
3.  **Database Interaction:** If validation passes, it creates a new `Transaction` SQLAlchemy model instance and commits it to the database.

```python
# backend/app/crud/crud_transaction.py

def create_with_portfolio(self, db: Session, *, obj_in: TransactionCreate, portfolio_id: int, user_id: int) -> Transaction:
    # ... validation logic ...
    db_obj = self.model(**obj_in.model_dump(), portfolio_id=portfolio_id, user_id=user_id)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
```

### Step 4: Response

The newly created `Transaction` object is returned from the CRUD layer, serialized by the `Transaction` Pydantic response schema, and sent back to the frontend as a JSON response with a `201 Created` status code.

---

This end-to-end flow demonstrates the separation of concerns and the clear path a request takes through the system, from user interaction to database persistence.