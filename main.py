from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="SkyNoid Cloud")

pending_command = None


class CommandRequest(BaseModel):
    command: str


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SkyNoid</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background: #07152b;
                color: white;
                padding: 30px;
            }

            h1 {
                font-size: 36px;
            }

            p {
                color: #b9c7dc;
            }

            button {
                display: block;
                width: 260px;
                margin: 18px auto;
                padding: 18px;
                font-size: 18px;
                border: none;
                border-radius: 12px;
                cursor: pointer;
            }
        </style>
    </head>

    <body>

        <h1>SkyNoid</h1>

        <p>What would you like to ask me?</p>

        <button onclick="sendCommand('TIME')">
            🕐 Current Time
        </button>

        <button onclick="sendCommand('DATE')">
            📅 Today's Date
        </button>

        <button onclick="sendCommand('DAY')">
            📆 Current Day
        </button>

        <p id="status"></p>

        <script>

        async function sendCommand(command) {

            document.getElementById("status").innerText =
                "Sending command to SkyNoid...";

            const response = await fetch("/command", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    command: command
                })
            });

            const data = await response.json();

            document.getElementById("status").innerText =
                "SkyNoid received: " + data.command;
        }

        </script>

    </body>
    </html>
    """


@app.post("/command")
def set_command(request: CommandRequest):

    global pending_command

    command = request.command.upper()

    allowed = ["TIME", "DATE", "DAY"]

    if command not in allowed:
        return {
            "status": "error",
            "message": "Unknown command"
        }

    pending_command = {
        "command": command,
        "created": datetime.now().isoformat()
    }

    print("[PHONE]", command)

    return {
        "status": "ok",
        "command": command
    }


@app.get("/robot/command")
def get_robot_command():

    global pending_command

    if pending_command is None:
        return {
            "command": None
        }

    command = pending_command

    pending_command = None

    return command


@app.get("/health")
def health():
    return {
        "status": "online"
    }

