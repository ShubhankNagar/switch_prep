# Single image serving the Angular UI and the Spring Boot API on port 8080.
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npx ng build

FROM maven:3.9-eclipse-temurin-21 AS api
WORKDIR /api
COPY backend/pom.xml .
RUN mvn -B -q dependency:go-offline
COPY backend/src ./src
COPY --from=web /web/dist/frontend/browser ./src/main/resources/static
RUN mvn -B -q package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=api /api/target/switchprep-api-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
