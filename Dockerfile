# Use a lightweight Node image
FROM node:18-alpine

# Create app directory
WORKDIR /app

# Copy package.json first to leverage Docker caching
COPY package.json .

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Expose port 3000 (the port your Node app will run on)
EXPOSE 3000

# Start the server
CMD ["node", "app.js"]