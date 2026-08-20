with open('frontend/src/components/common/LoadingButton.tsx', 'r') as f:
    content = f.read()

new_content = content.replace("      {isLoading && <ArrowPathIcon className=\"h-4 w-4 animate-spin\" aria-hidden=\"true\" />}", "      {isLoading && <ArrowPathIcon className=\"h-4 w-4 animate-spin\" aria-hidden=\"true\" />}\n      {isLoading && !loadingText && <span className=\"sr-only\">Loading...</span>}")

with open('frontend/src/components/common/LoadingButton.tsx', 'w') as f:
    f.write(new_content)
