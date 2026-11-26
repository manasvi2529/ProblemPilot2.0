import asyncio
import httpx
from httpx import ASGITransport
from backend.main import app
from backend.security import create_access_token

async def test_concurrency_and_rate_limits():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Fire 20 parallel requests to /api/auth/me without token -> should all be 401
        tasks = [client.get("/api/auth/me") for _ in range(20)]
        results = await asyncio.gather(*tasks)
        statuses = [r.status_code for r in results]
        print("Concurrent unauthenticated requests:", set(statuses))

        # 2. Fire 30 rapid requests to /api/auth/login from same client IP -> rate limiter should trigger 429
        login_tasks = [client.post("/api/auth/login", json={"email": "none@example.com", "password": "wrong"}) for _ in range(30)]
        login_results = await asyncio.gather(*login_tasks)
        login_statuses = [r.status_code for r in login_results]
        print("Login status distribution (rate limiting):", {s: login_statuses.count(s) for s in set(login_statuses)})

if __name__ == "__main__":
    asyncio.run(test_concurrency_and_rate_limits())
