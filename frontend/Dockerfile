# Node.js 20+ required for Vite 7.x (uses crypto.hash API)
FROM node:20-alpine

WORKDIR /app

# Copy package.json and install dependencies
# This is done in a separate step to leverage Docker layer caching
RUN npm install -g pnpm
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile && npx update-browserslist-db@latest -y

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 3000

CMD ["pnpm", "run", "dev", "--", "--host"]