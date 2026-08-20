with open('frontend/src/pages/WatchlistsPage.tsx', 'r') as f:
    content = f.read()

new_content = content.replace("<WatchlistEmptyState />", "<WatchlistEmptyState onCreateClick={() => document.querySelector<HTMLButtonElement>('[aria-label=\"Add new watchlist\"]')?.click()} />")

with open('frontend/src/pages/WatchlistsPage.tsx', 'w') as f:
    f.write(new_content)
