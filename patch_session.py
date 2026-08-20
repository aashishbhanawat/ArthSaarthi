with open('frontend/src/components/modals/SessionTimeoutModal.tsx', 'r') as f:
    content = f.read()

new_content = content.replace("            <button\n              onClick={onClose}\n              className=\"btn btn-secondary\"\n            >\n              Stay Logged In\n            </button>", "            <button\n              type=\"button\"\n              onClick={onClose}\n              className=\"btn btn-secondary\"\n            >\n              Stay Logged In\n            </button>")
new_content = new_content.replace("            <button\n              onClick={onLogout}\n              className=\"btn btn-danger\"\n            >\n              Logout\n            </button>", "            <button\n              type=\"button\"\n              onClick={onLogout}\n              className=\"btn btn-danger\"\n            >\n              Logout\n            </button>")

with open('frontend/src/components/modals/SessionTimeoutModal.tsx', 'w') as f:
    f.write(new_content)
