import os
import uuid
from datetime import datetime
from collections import deque

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


app = FastAPI(title="SkyNoid Cloud")


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROBOT_ID = "SKYNOID_01"

ROBOT_KEY = os.getenv("SKYNOID_ROBOT_KEY")

if not ROBOT_KEY:
    print("[WARNING] SKYNOID_ROBOT_KEY is not configured.")


# --------------------------------------------------
# COMMAND QUEUE
# --------------------------------------------------

command_queue = deque()

command_history = {}


class CommandRequest(BaseModel):
    command: str


# --------------------------------------------------
# PHONE INTERFACE
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <title>SkyNoid</title>

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <style>

            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background: #07152b;
                color: white;
                padding: 30px;
            }

            h1 {
                font-size: 38px;
                margin-bottom: 5px;
            }

            .subtitle {
                color: #b9c7dc;
                margin-bottom: 30px;
            }

            button {
                display: block;
                width: 280px;
                margin: 18px auto;
                padding: 18px;
                font-size: 18px;
                border: none;
                border-radius: 12px;
                cursor: pointer;
            }

            button:active {
                transform: scale(0.98);
            }

            #status {
                margin-top: 30px;
                color: #8fd3ff;
            }

        </style>

    </head>


    <body>

        <h1>SkyNoid</h1>

        <p class="subtitle">
            What would you like to ask me?
        </p>


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

                const status =
                    document.getElementById("status");

                status.innerText =
                    "Sending command to SkyNoid...";


                try {

                    const response =
                        await fetch("/command", {

                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                command: command
                            })

                        });


                    const data =
                        await response.json();


                    if (data.status === "queued") {

                        status.innerText =
                            "Sent to SkyNoid: " +
                            data.command;

                    } else {

                        status.innerText =
                            "Unable to send command.";

                    }

                }

                catch (error) {

                    status.innerText =
                        "Connection error.";

                }

            }

        </script>

    </body>

    </html>
    """


# --------------------------------------------------
# PHONE SENDS COMMAND
# --------------------------------------------------

@app.post("/command")
def create_command(request: CommandRequest):

    command = request.command.strip().upper()

    allowed_commands = {
        "TIME",
        "DATE",
        "DAY"
    }


    if command not in allowed_commands:

        raise HTTPException(
            status_code=400,
            detail="Unknown command"
        )


    command_id = str(uuid.uuid4())


    item = {

        "id": command_id,

        "robot_id": ROBOT_ID,

        "command": command,

        "status": "pending",

        "created_at":
            datetime.now().isoformat(),

        "completed_at": None
    }


    command_queue.append(item)

    command_history[command_id] = item


    print(
        f"[QUEUE] Added {command} "
        f"id={command_id}"
    )


    return {

        "status": "queued",

        "id": command_id,

        "command": command
    }


# --------------------------------------------------
# ROBOT AUTHENTICATION
# --------------------------------------------------

def authenticate_robot(
    authorization: str | None
):

    if not ROBOT_KEY:

        raise HTTPException(
            status_code=500,
            detail="Robot key not configured"
        )


    expected = f"Bearer {ROBOT_KEY}"


    if authorization != expected:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized robot"
        )


# --------------------------------------------------
# ROBOT REQUESTS NEXT COMMAND
# --------------------------------------------------

@app.get("/robot/command")
def get_robot_command(
    authorization: str | None =
        Header(default=None)
):

    authenticate_robot(authorization)


    if not command_queue:

        return {
            "command": None
        }


    item = command_queue.popleft()

    item["status"] = "processing"


    print(
        f"[ROBOT] Sending "
        f"{item['command']} "
        f"id={item['id']}"
    )


    return item


# --------------------------------------------------
# ROBOT ACKNOWLEDGES COMPLETION
# --------------------------------------------------

@app.post("/robot/ack/{command_id}")
def acknowledge_command(
    command_id: str,
    authorization: str | None =
        Header(default=None)
):

    authenticate_robot(authorization)


    item = command_history.get(command_id)


    if not item:

        raise HTTPException(
            status_code=404,
            detail="Command not found"
        )


    item["status"] = "completed"

    item["completed_at"] = (
        datetime.now().isoformat()
    )


    print(
        f"[ROBOT] Completed "
        f"{item['command']} "
        f"id={command_id}"
    )


    return {
        "status": "completed",
        "id": command_id
    }


# --------------------------------------------------
# COMMAND STATUS
# --------------------------------------------------

@app.get("/command/{command_id}")
def command_status(command_id: str):

    item = command_history.get(command_id)


    if not item:

        raise HTTPException(
            status_code=404,
            detail="Command not found"
        )


    return item


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "online",
        "robot": ROBOT_ID,
        "queue_length": len(command_queue)
    }
