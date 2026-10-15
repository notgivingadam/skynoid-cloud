import os
import uuid
from collections import deque
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


# ============================================================
# SKYNOID CLOUD SERVER
# ============================================================

app = FastAPI(
    title="SkyNoid Cloud",
    description="Cloud command interface for the SkyNoid robot",
    version="2.0"
)


# ============================================================
# CONFIGURATION
# ============================================================

ROBOT_ID = "SKYNOID_01"

ROBOT_KEY = os.getenv("SKYNOID_ROBOT_KEY")

if not ROBOT_KEY:
    print(
        "[WARNING] SKYNOID_ROBOT_KEY environment variable "
        "is not configured."
    )


# ============================================================
# COMMAND STORAGE
# ============================================================

command_queue = deque()

command_history = {}


# ============================================================
# ALLOWED COMMANDS
# ============================================================

ALLOWED_COMMANDS = {
    "TIME",
    "DATE",
    "DAY",
    "ABOUT_SKYNOID",
    "ABOUT_DRONES",
    "ABOUT_SKYNOVA",
}


# ============================================================
# REQUEST MODEL
# ============================================================

class CommandRequest(BaseModel):
    command: str


# ============================================================
# ROBOT AUTHENTICATION
# ============================================================

def authenticate_robot(authorization: str | None):

    if not ROBOT_KEY:
        raise HTTPException(
            status_code=500,
            detail="Robot key is not configured on server"
        )

    expected = f"Bearer {ROBOT_KEY}"

    if authorization != expected:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized robot"
        )


# ============================================================
# WEB INTERFACE
# ============================================================

@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>SkyNoid</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;

            font-family:
                Arial,
                Helvetica,
                sans-serif;

            background:
                linear-gradient(
                    135deg,
                    #07152e,
                    #102b52
                );

            color: white;

            display: flex;
            justify-content: center;
            align-items: center;

            padding: 20px;
        }


        .container {

            width: 100%;
            max-width: 500px;

            background:
                rgba(255, 255, 255, 0.08);

            border:
                1px solid
                rgba(255, 255, 255, 0.15);

            border-radius: 24px;

            padding: 30px 22px;

            box-shadow:
                0 15px 45px
                rgba(0, 0, 0, 0.35);

            text-align: center;
        }


        .robot-icon {

            font-size: 55px;

            margin-bottom: 5px;
        }


        h1 {

            margin:
                5px 0 5px 0;

            font-size: 34px;

            letter-spacing: 2px;
        }


        .subtitle {

            color: #c8d9ef;

            margin-bottom: 28px;

            font-size: 16px;
        }


        .button {

            width: 100%;

            padding:
                16px 18px;

            margin:
                8px 0;

            border: none;

            border-radius: 14px;

            background: white;

            color: #102b52;

            font-size: 16px;

            font-weight: bold;

            cursor: pointer;

            transition:
                transform 0.15s,
                background 0.15s;
        }


        .button:hover {

            transform:
                translateY(-2px);

            background:
                #eaf3ff;
        }


        .button:active {

            transform:
                scale(0.98);
        }


        #status {

            min-height: 24px;

            margin-top: 20px;

            color: #b9dcff;

            font-size: 14px;
        }


        .footer {

            margin-top: 25px;

            font-size: 12px;

            color: #8faac8;
        }

    </style>

</head>


<body>

    <div class="container">

        <div class="robot-icon">
            🤖
        </div>

        <h1>
            SKYNOID
        </h1>

        <div class="subtitle">
            What would you like to ask me?
        </div>


        <button
            class="button"
            onclick="sendCommand('TIME')"
        >
            🕐 Tell me the current time
        </button>


        <button
            class="button"
            onclick="sendCommand('DATE')"
        >
            📅 Tell me today's date
        </button>


        <button
            class="button"
            onclick="sendCommand('DAY')"
        >
            📆 Tell me what day it is
        </button>


        <button
            class="button"
            onclick="sendCommand('ABOUT_SKYNOID')"
        >
            🤖 Tell me about SkyNoid
        </button>


        <button
            class="button"
            onclick="sendCommand('ABOUT_DRONES')"
        >
            🚁 Tell me about Drones
        </button>


        <button
            class="button"
            onclick="sendCommand('ABOUT_SKYNOVA')"
        >
            🏢 Tell me about SkyNova Drones
        </button>


        <div id="status">
            SkyNoid is ready.
        </div>


        <div class="footer">
            SkyNova Drones
        </div>

    </div>


    <script>

        async function sendCommand(command) {

            const status =
                document.getElementById("status");

            status.innerText =
                "Sending request to SkyNoid...";


            try {

                const response =
                    await fetch(
                        "/command",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    command: command
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    status.innerText =
                        data.detail ||
                        "Unable to send command.";

                    return;
                }


                status.innerText =
                    "Request sent to SkyNoid.";

            }

            catch (error) {

                status.innerText =
                    "Unable to connect to SkyNoid.";

            }

        }

    </script>

</body>

</html>
"""


# ============================================================
# PUBLIC COMMAND SUBMISSION
# ============================================================

@app.post("/command")
def submit_command(request: CommandRequest):

    command = request.command.strip().upper()

    if command not in ALLOWED_COMMANDS:

        raise HTTPException(
            status_code=400,
            detail="Invalid SkyNoid command"
        )


    command_id = str(uuid.uuid4())


    item = {

        "id": command_id,

        "command": command,

        "status": "pending",

        "created_at":
            datetime.utcnow().isoformat()

    }


    command_queue.append(item)

    command_history[command_id] = item


    print(
        f"[QUEUE] Added: "
        f"{command} | {command_id}"
    )


    return {

        "success": True,

        "id": command_id,

        "command": command,

        "status": "pending"

    }


# ============================================================
# ROBOT GETS NEXT COMMAND
# ============================================================

@app.get("/robot/command")
def get_robot_command(
    authorization: str | None = Header(default=None)
):

    authenticate_robot(authorization)


    if not command_queue:

        return {
            "command": None
        }


    item = command_queue.popleft()


    item["status"] = "processing"

    item["processing_at"] = (
        datetime.utcnow().isoformat()
    )


    command_history[item["id"]] = item


    print(
        f"[ROBOT] Sending: "
        f"{item['command']} | {item['id']}"
    )


    return {

        "id": item["id"],

        "command": item["command"],

        "status": item["status"]

    }


# ============================================================
# ROBOT ACKNOWLEDGES COMPLETED COMMAND
# ============================================================

@app.post("/robot/ack/{command_id}")
def acknowledge_command(
    command_id: str,
    authorization: str | None = Header(default=None)
):

    authenticate_robot(authorization)


    if command_id not in command_history:

        raise HTTPException(
            status_code=404,
            detail="Command not found"
        )


    item = command_history[command_id]


    item["status"] = "completed"

    item["completed_at"] = (
        datetime.utcnow().isoformat()
    )


    command_history[command_id] = item


    print(
        f"[ACK] Completed: "
        f"{item['command']} | {command_id}"
    )


    return {

        "success": True,

        "id": command_id,

        "status": "completed"

    }


# ============================================================
# COMMAND STATUS
# ============================================================

@app.get("/command/{command_id}")
def command_status(command_id: str):

    if command_id not in command_history:

        raise HTTPException(
            status_code=404,
            detail="Command not found"
        )


    return command_history[command_id]


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "online",

        "robot": ROBOT_ID,

        "queue_length":
            len(command_queue),

        "available_commands":
            len(ALLOWED_COMMANDS)

    }
