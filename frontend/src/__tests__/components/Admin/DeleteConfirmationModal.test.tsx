import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { DeleteConfirmationModal } from "../../../components/common/DeleteConfirmationModal";
import { User } from "../../../types/user";

const mockUser: User = {
  id: "user-123",
  email: "test@example.com",
  full_name: "Test User",
  is_active: true,
  is_admin: false,
};

describe("DeleteConfirmationModal", () => {
  const onConfirm = jest.fn();
  const onClose = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = () => {
    render(
      <DeleteConfirmationModal
        isOpen={true}
        onClose={onClose}
        onConfirm={onConfirm}
        title="Delete User"
        message={
          <p>
            Are you sure you want to delete the user{" "}
            <strong>{mockUser.email}</strong>?
          </p>
        }
        isDeleting={false}
      />,
    );
  };

  test("renders the confirmation message with the user name", () => {
    renderComponent();
    expect(
      screen.getByRole("heading", { name: "Delete User" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/are you sure you want to delete the user/i),
    ).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  test("calls onConfirm when the Delete button is clicked", () => {
    renderComponent();
    fireEvent.click(screen.getByRole("button", { name: "Confirm Delete" }));
    expect(onConfirm).toHaveBeenCalled();
  });

  test("calls onClose when the Cancel button is clicked", () => {
    renderComponent();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onClose).toHaveBeenCalled();
  });

  test("calls onClose when the close icon button is clicked", () => {
    renderComponent();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalled();
  });

  test("shows loading state when isDeleting is true", () => {
    render(
      <DeleteConfirmationModal
        isOpen={true}
        onClose={onClose}
        onConfirm={onConfirm}
        title="Delete User"
        message="Message"
        isDeleting={true}
      />,
    );
    expect(
      screen.getByRole("button", { name: /deleting/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Deleting...")).toBeInTheDocument();
  });
});
