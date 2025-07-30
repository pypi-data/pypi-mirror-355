from nexios import NexiosApp
import uvicorn

app = NexiosApp()

@app.route("/")
async def index(req, res):
    return res.json({"message": "Hello, World!"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)