# Service A

Entry point of the demo chain. Receives a request and calls Service B.

See the [top-level README](../README.md) for full deployment instructions.

## Endpoints

| Method | Path     | Description                                      |
|--------|----------|--------------------------------------------------|
| GET    | `/`      | Health check                                     |
| GET    | `/hello` | Calls Service B and returns the full chain reply |

## Environment variables

| Variable        | Required | Description                                        |
|-----------------|----------|----------------------------------------------------|
| `SERVICE_TOKEN` | Yes      | Shared secret for authenticating service requests  |
| `SERVICE_B_URL` | Yes      | Vanity URL of Service B, e.g. `https://<host>/apps/demo-service-b` |
| `PORT`          | No       | Port to listen on (default: `8888`)                |
| `VERIFY_SSL`    | No       | Set to `false` to disable SSL verification (not recommended in production) |
