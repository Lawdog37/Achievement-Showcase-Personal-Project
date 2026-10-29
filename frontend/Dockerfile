# The frontend is built in two stages ("multi-stage build"):
#   1. a Node container compiles the React app into plain HTML/CSS/JS files
#   2. a tiny nginx web server container serves those files
# Node and node_modules never make it into the final image, so it stays small.

# ---- Stage 1: build ----
FROM node:25-alpine AS build
WORKDIR /app

# Install packages first (cached until package-lock.json changes)
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Stage 2: serve ----
FROM nginx:1.30-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
