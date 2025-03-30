from locust import HttpUser, task, between

class LinkShortenerUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def create_short_link(self):
        self.client.post(
            "/links/shorten",
            json={"original_url": "https://load.test"}
        )