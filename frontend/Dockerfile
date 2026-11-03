# One file, several stages; each FROM starts a new one.
#   docker build frontend                -> prod: nginx with the built app (the last stage is the default)
#   docker build --target dev frontend   -> the Vite dev server, for docker-compose during development

# Keep in step with .nvmrc
ARG NODE_VERSION=22

# --- deps: the packages, shared by the dev server and the build.
# Copying only the package files first lets Docker reuse this layer until they change,
# so editing the code doesn't download every package again.
FROM node:${NODE_VERSION}-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# --- dev: the source code is mounted from the host, so changes show up right away
FROM deps AS dev
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --- build: type check and build the static files into /app/dist
FROM deps AS build
COPY . .
RUN npm run build

# --- prod: nginx serves the built files and passes /api and /ws on to the backend.
# Nothing of Node gets here: the image holds only nginx and the few files from dist.
FROM nginx:1.29-alpine AS prod
# Where the backend is; nginx's image puts it into the config when the container starts
ENV BACKEND_URL=http://backend:8000
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
