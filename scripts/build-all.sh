#!/usr/bin/env bash
# Builds the Angular app and packages it inside the Spring Boot jar, so one process serves UI + API.
# Output: backend/target/switchprep-api-1.0.0.jar  (run with: java -jar backend/target/switchprep-api-1.0.0.jar)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT/frontend"
npm ci
npx ng build

rm -rf "$ROOT/backend/src/main/resources/static"
mkdir -p "$ROOT/backend/src/main/resources/static"
cp -r "$ROOT/frontend/dist/frontend/browser/." "$ROOT/backend/src/main/resources/static/"

cd "$ROOT/backend"
mvn -B package
echo "Built backend/target/switchprep-api-1.0.0.jar"
