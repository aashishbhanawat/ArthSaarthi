FROM node:18-alpine

WORKDIR /app

# Copy package.json and install dependencies
# This is done in a separate step to leverage Docker layer caching
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 3000

CMD ["npm", "run", "dev"]