from locust import HttpUser, TaskSet, task, between
import random
import string

class UserBehavior(TaskSet):

    @task(2)
    def create_short_link(self):
        # Generate a random URL for testing
        random_url = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        self.client.post("/links/shorten", json={"url": f"http://example.com/{random_url}"})

    @task(1)
    def redirect_to_original_url(self):
        # First, create a short link
        random_url = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        response = self.client.post("/links/shorten", json={"url": f"http://example.com/{random_url}"})
        if response.status_code == 200:
            data = response.json()
            short_link = data.get("short_link")
            if short_link:
                # Then, try to redirect using the short link
                self.client.get(f"/links/{short_link}", name="/links/[short_link]")

    @task(1)
    def get_expired_links(self):
        self.client.get("/links/expired")

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 5)  # Simulate a user waiting time between 1 to 5 seconds

# Run Locust with: locust -f locustfile.py --host=http://localhost:8000