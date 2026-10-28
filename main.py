import os
import uuid
import re

from collections import deque
from datetime import datetime, timedelta

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel


# ============================================================
# SKYNOID CLOUD SERVER
# ============================================================

app = FastAPI(
    title="SkyNoid Cloud",
    description="Cloud command interface for the SkyNoid robot",
    version="2.2"
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
    "PLAY_SONG",
    "STOP_MUSIC",
    "SET_MEDICINE_REMINDER",
    "DIRECTION",
}


# ============================================================
# ALLOWED SONGS
# ============================================================

ALLOWED_SONGS = {
    "NATIONAL_ANTHEM",
    "MERRY_CHRISTMAS",
    "JINGLE_BELLS",
    "BENGALI_SONG",
    "BA_BA_BLACK_SHEEP",
}


# ============================================================
# ALLOWED REPEAT TYPES
# ============================================================

ALLOWED_REPEAT_TYPES = {
    "once",
    "daily",
    "weekdays",
    "selected",
}


ALLOWED_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}


# ============================================================
# REQUEST MODEL
# ============================================================

class CommandRequest(BaseModel):
    command: str
    payload: dict | None = None


# ============================================================
# ROBOT AUTHENTICATION
# ============================================================

def authenticate_robot(
    authorization: str | None
):

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

@app.get(
    "/",
    response_class=HTMLResponse
)
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


        h2 {

            margin:
                8px 0 5px 0;

            font-size: 27px;
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


        .medicine-button {

            background: #e8fff0;

            color: #155b31;
        }


        .stop-button {

            background: #ffe8e8;

            color: #8a2020;
        }


        .back-button {

            background:
                rgba(255, 255, 255, 0.15);

            color: white;

            border:
                1px solid
                rgba(255, 255, 255, 0.25);
        }


        .form-group {

            text-align: left;

            margin:
                15px 0;
        }


        .form-group label {

            display: block;

            margin-bottom: 7px;

            color: #dcecff;

            font-size: 14px;

            font-weight: bold;
        }


        .form-control {

            width: 100%;

            padding:
                13px 14px;

            border: none;

            border-radius: 11px;

            background:
                rgba(255, 255, 255, 0.96);

            color: #102b52;

            font-size: 16px;

            outline: none;
        }


        .form-control:focus {

            box-shadow:
                0 0 0 3px
                rgba(120, 184, 255, 0.35);
        }


        .help-text {

            color: #a9c5e5;

            font-size: 12px;

            margin-top: 6px;
        }


        .reminder-badge {

            margin:
                15px 0;

            padding:
                12px;

            border-radius:
                12px;

            background:
                rgba(80, 220, 130, 0.12);

            border:
                1px solid
                rgba(100, 240, 150, 0.25);

            color:
                #c8ffd9;

            font-size:
                14px;
        }


        .days-container {

            display: none;

            grid-template-columns:
                repeat(2, 1fr);

            gap: 8px;

            margin-top: 8px;
        }


        .day-option {

            display: flex;

            align-items: center;

            gap: 7px;

            background:
                rgba(255, 255, 255, 0.1);

            padding:
                10px;

            border-radius:
                9px;

            color:
                white;

            font-size:
                13px;
        }


        #onceDateGroup {

            display: none;
        }


        #status {

            min-height: 24px;

            margin-top: 20px;

            color: #b9dcff;

            font-size: 14px;

            line-height: 1.4;
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


        <!-- ================================================= -->
        <!-- MAIN MENU                                         -->
        <!-- ================================================= -->

        <div id="mainMenu">

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


            <button
                class="button"
                onclick="showSongMenu()"
            >
                🎵 Play a Song
            </button>


            <button
                class="button"
                onclick="showDirectionMenu()"
            >
                🧭 Direction Guidance
            </button>


            <button
                class="button"
                onclick="showMedicineMenu()"
            >
                💊 Medicine Reminder
            </button>

        </div>


        <!-- ================================================= -->
        <!-- SONG MENU                                         -->
        <!-- ================================================= -->

        <div
            id="songMenu"
            style="display: none;"
        >

            <h2>
                🎵 PLAY A SONG
            </h2>

            <div class="subtitle">
                Select a song for SkyNoid
            </div>


            <button
                class="button"
                onclick="playSong('NATIONAL_ANTHEM')"
            >
                🇮🇳 National Anthem
            </button>


            <button
                class="button"
                onclick="playSong('MERRY_CHRISTMAS')"
            >
                🎄 Merry Christmas
            </button>


            <button
                class="button"
                onclick="playSong('JINGLE_BELLS')"
            >
                🔔 Jingle Bells
            </button>


            <button
                class="button"
                onclick="playSong('BENGALI_SONG')"
            >
                🎵 Bengali Song
            </button>


            <button
                class="button"
                onclick="playSong('BA_BA_BLACK_SHEEP')"
            >
                🐑 Ba Ba Black Sheep
            </button>


            <button
                class="button stop-button"
                onclick="stopMusic()"
            >
                ⏹ Stop Music
            </button>


            <button
                class="button back-button"
                onclick="showMainMenu()"
            >
                ← Back to Menu
            </button>

        </div>


        <!-- ================================================= -->
        <!-- DIRECTION GUIDANCE MENU                           -->
        <!-- ================================================= -->

        <div id="directionMenu" style="display: none;">

            <h2>
                🧭 DIRECTION GUIDANCE
            </h2>

            <div class="subtitle">
                Where would you like to go?
            </div>

            <button class="button" onclick="requestDirection('director office')">
                🏢 Director's Office
            </button>

            <button class="button" onclick="requestDirection('balcony')">
                🌿 Balcony
            </button>

            <button class="button" onclick="requestDirection('washroom')">
                🚻 Washroom
            </button>

            <button class="button back-button" onclick="showMainMenu()">
                ← Back to Menu
            </button>

        </div>


        <!-- ================================================= -->
        <!-- MEDICINE REMINDER MENU                            -->
        <!-- ================================================= -->

        <div
            id="medicineMenu"
            style="display: none;"
        >

            <h2>
                💊 MEDICINE REMINDER
            </h2>

            <div class="subtitle">
                Set a medicine reminder with SkyNoid
            </div>


            <div class="reminder-badge">
                🔔 SkyNoid will remind you
                10 minutes before medicine time.
            </div>


            <div class="form-group">

                <label for="person">
                    Person
                </label>

                <input
                    id="person"
                    class="form-control"
                    type="text"
                    placeholder="e.g. SkyNoid"
                >

            </div>


            <div class="form-group">

                <label for="medicine">
                    Medicine name
                </label>

                <input
                    id="medicine"
                    class="form-control"
                    type="text"
                    placeholder="e.g. Vitamin D"
                >

            </div>


            <div class="form-group">

                <label for="instruction">
                    Dose / Instruction
                </label>

                <input
                    id="instruction"
                    class="form-control"
                    type="text"
                    placeholder="e.g. Take one tablet"
                >

                <div class="help-text">
                    Optional
                </div>

            </div>


            <div class="form-group">

                <label for="medicineTime">
                    Medicine time
                </label>

                <input
                    id="medicineTime"
                    class="form-control"
                    type="time"
                >

            </div>


            <div class="form-group">

                <label for="repeatType">
                    Repeat
                </label>

                <select
                    id="repeatType"
                    class="form-control"
                    onchange="repeatChanged()"
                >

                    <option value="once">
                        Once
                    </option>

                    <option value="daily">
                        Every day
                    </option>

                    <option value="weekdays">
                        Monday - Friday
                    </option>

                    <option value="selected">
                        Selected days
                    </option>

                </select>

            </div>


            <!-- ONCE DATE -->

            <div
                class="form-group"
                id="onceDateGroup"
            >

                <label for="medicineDate">
                    Date
                </label>

                <input
                    id="medicineDate"
                    class="form-control"
                    type="date"
                >

            </div>


            <!-- SELECTED DAYS -->

            <div
                class="form-group"
                id="selectedDaysGroup"
                style="display: none;"
            >

                <label>
                    Select days
                </label>


                <div
                    class="days-container"
                    id="daysContainer"
                >

                    <label class="day-option">
                        <input
                            type="checkbox"
                            value="monday"
                            class="medicine-day"
                        >
                        Monday
                    </label>


                    <label class="day-option">
                        <input
                            type="checkbox"
                            value="tuesday"
                            class="medicine-day"
                        >
                        Tuesday
                    </label>


                    <label class="day-option">
                        <input
                            type="checkbox"
                            value="wednesday"
                            class="medicine-day"
                        >
                        Wednesday
                    </label>


                    <label class="day-option">
                        <input
                            type="checkbox"
                            value="thursday"
                            class="medicine-day"
                        >
                        Thursday
                    </label>


                    <label class="day-option">
                        <input
                            type="checkbox"
                            value="friday"
                            class="medicine-day"
                        >
                        Friday
                    </label>


                    <label class="day-option">
                        <input
                            type="checkbox"
                            value="saturday"
                            class="medicine-day"
                        >
                        Saturday
                    </label>


                    <label class="day-option">
                        <input
                            type="checkbox"
                            value="sunday"
                            class="medicine-day"
                        >
                        Sunday
                    </label>

                </div>

            </div>


            <button
                class="button medicine-button"
                onclick="setMedicineReminder()"
            >
                💊 Set Medicine Reminder
            </button>


            <button
                class="button"
                onclick="downloadMedicineCalendar()"
            >
                📱 Add to Phone Calendar
            </button>


            <button
                class="button back-button"
                onclick="showMainMenu()"
            >
                ← Back to Menu
            </button>

        </div>


        <div id="status">
            SkyNoid is ready.
        </div>


        <div class="footer">
            SkyNova Drones
        </div>

    </div>


    <script>

        // ====================================================
        // SHOW MAIN MENU
        // ====================================================

        function showMainMenu() {

            document.getElementById(
                "mainMenu"
            ).style.display = "block";


            document.getElementById(
                "songMenu"
            ).style.display = "none";

            document.getElementById(
                "directionMenu"
            ).style.display = "none";


            document.getElementById(
                "medicineMenu"
            ).style.display = "none";

            document.getElementById(
                "directionMenu"
            ).style.display = "none";


            document.getElementById(
                "status"
            ).innerText =
                "SkyNoid is ready.";
        }


        // ====================================================
        // SHOW SONG MENU
        // ====================================================

        function showSongMenu() {

            document.getElementById(
                "mainMenu"
            ).style.display = "none";


            document.getElementById(
                "medicineMenu"
            ).style.display = "none";

            document.getElementById(
                "directionMenu"
            ).style.display = "none";


            document.getElementById(
                "songMenu"
            ).style.display = "block";


            document.getElementById(
                "status"
            ).innerText =
                "Select a song.";
        }


        // ====================================================
        // SHOW MEDICINE MENU
        // ====================================================

        function showMedicineMenu() {

            document.getElementById(
                "mainMenu"
            ).style.display = "none";


            document.getElementById(
                "songMenu"
            ).style.display = "none";


            document.getElementById(
                "medicineMenu"
            ).style.display = "block";


            document.getElementById(
                "status"
            ).innerText =
                "Enter the medicine details.";


            repeatChanged();
        }


        // ====================================================
        // DIRECTION GUIDANCE
        // ====================================================

        function showDirectionMenu() {
            document.getElementById("mainMenu").style.display = "none";
            document.getElementById("songMenu").style.display = "none";
            document.getElementById("medicineMenu").style.display = "none";
            document.getElementById("directionMenu").style.display = "block";
            document.getElementById("status").innerText = "Select a destination.";
        }

        function requestDirection(destination) {
            sendCommand(
                "DIRECTION",
                { destination: destination }
            );
        }


        // ====================================================
        // REPEAT TYPE CHANGED
        // ====================================================

        function repeatChanged() {

            const repeat =
                document.getElementById(
                    "repeatType"
                ).value;


            const onceDateGroup =
                document.getElementById(
                    "onceDateGroup"
                );


            const selectedDaysGroup =
                document.getElementById(
                    "selectedDaysGroup"
                );


            const daysContainer =
                document.getElementById(
                    "daysContainer"
                );


            if (repeat === "once") {

                onceDateGroup.style.display =
                    "block";

            }

            else {

                onceDateGroup.style.display =
                    "none";

            }


            if (repeat === "selected") {

                selectedDaysGroup.style.display =
                    "block";

                daysContainer.style.display =
                    "grid";

            }

            else {

                selectedDaysGroup.style.display =
                    "none";

                daysContainer.style.display =
                    "none";

            }
        }


        // ====================================================
        // PLAY SONG
        // ====================================================

        function playSong(song) {

            sendCommand(
                "PLAY_SONG",
                {
                    song: song
                }
            );
        }


        // ====================================================
        // STOP MUSIC
        // ====================================================

        function stopMusic() {

            sendCommand(
                "STOP_MUSIC"
            );
        }


        // ====================================================
        // SET MEDICINE REMINDER
        // ====================================================

        async function setMedicineReminder() {

            const status =
                document.getElementById(
                    "status"
                );


            const person =
                document.getElementById(
                    "person"
                ).value.trim();


            const medicine =
                document.getElementById(
                    "medicine"
                ).value.trim();


            const instruction =
                document.getElementById(
                    "instruction"
                ).value.trim();


            const time =
                document.getElementById(
                    "medicineTime"
                ).value;


            const repeat =
                document.getElementById(
                    "repeatType"
                ).value;


            const date =
                document.getElementById(
                    "medicineDate"
                ).value;


            const selectedDays = [];


            document.querySelectorAll(
                ".medicine-day:checked"
            ).forEach(
                function(item) {

                    selectedDays.push(
                        item.value
                    );
                }
            );


            // -----------------------------------------------
            // VALIDATION
            // -----------------------------------------------

            if (!person) {

                status.innerText =
                    "Please enter the person's name.";

                return;
            }


            if (!medicine) {

                status.innerText =
                    "Please enter the medicine name.";

                return;
            }


            if (!time) {

                status.innerText =
                    "Please select the medicine time.";

                return;
            }


            if (
                repeat === "once"
                && !date
            ) {

                status.innerText =
                    "Please select the medicine date.";

                return;
            }


            if (
                repeat === "selected"
                && selectedDays.length === 0
            ) {

                status.innerText =
                    "Please select at least one day.";

                return;
            }


            const payload = {

                person: person,

                medicine: medicine,

                instruction: instruction,

                time: time,

                repeat: repeat,

                date:
                    repeat === "once"
                        ? date
                        : null,

                selected_days:
                    repeat === "selected"
                        ? selectedDays
                        : []
            };


            status.innerText =
                "Setting medicine reminder...";


            const success =
                await sendCommand(
                    "SET_MEDICINE_REMINDER",
                    payload
                );


            if (success) {

                status.innerText =
                    "Medicine reminder sent to SkyNoid. "
                    + "SkyNoid will remind you "
                    + "10 minutes before medicine time.";
            }
        }


        // ====================================================
        // DOWNLOAD PHONE CALENDAR
        // ====================================================

        function downloadMedicineCalendar() {
            const status = document.getElementById("status");
            const person = document.getElementById("person").value.trim();
            const medicine = document.getElementById("medicine").value.trim();
            const instruction = document.getElementById("instruction").value.trim();
            const time = document.getElementById("medicineTime").value;
            const repeat = document.getElementById("repeatType").value;
            const date = document.getElementById("medicineDate").value;
            const selectedDays = [];

            document.querySelectorAll(".medicine-day:checked").forEach(
                function(item) {
                    selectedDays.push(item.value);
                }
            );

            if (!person) {
                status.innerText = "Please enter the person's name.";
                return;
            }
            if (!medicine) {
                status.innerText = "Please enter the medicine name.";
                return;
            }
            if (!time) {
                status.innerText = "Please select the medicine time.";
                return;
            }
            if (repeat === "once" && !date) {
                status.innerText = "Please select the medicine date.";
                return;
            }
            if (repeat === "selected" && selectedDays.length === 0) {
                status.innerText = "Please select at least one day.";
                return;
            }

            const params = new URLSearchParams({
                person: person,
                medicine: medicine,
                instruction: instruction,
                time: time,
                repeat: repeat,
                date: date,
                selected_days: selectedDays.join(",")
            });

            status.innerText = "Creating phone calendar file...";
            window.location.href = "/calendar?" + params.toString();
        }


        // ====================================================
        // SEND COMMAND
        // ====================================================

        async function sendCommand(
            command,
            payload = {}
        ) {

            const status =
                document.getElementById(
                    "status"
                );


            if (
                command ===
                "PLAY_SONG"
            ) {

                status.innerText =
                    "Asking SkyNoid to play the song...";

            }

            else if (
                command ===
                "STOP_MUSIC"
            ) {

                status.innerText =
                    "Stopping music...";

            }

            else if (
                command ===
                "SET_MEDICINE_REMINDER"
            ) {

                status.innerText =
                    "Sending medicine reminder to SkyNoid...";

            }

            else if (
                command === "DIRECTION"
            ) {

                status.innerText =
                    "Asking SkyNoid for directions...";

            }

            else {

                status.innerText =
                    "Sending request to SkyNoid...";

            }


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
                                    command: command,
                                    payload: payload
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    status.innerText =
                        data.detail
                        ||
                        "Unable to send command.";

                    return false;
                }


                if (
                    command ===
                    "PLAY_SONG"
                ) {

                    status.innerText =
                        "Song request sent to SkyNoid.";

                }

                else if (
                    command ===
                    "STOP_MUSIC"
                ) {

                    status.innerText =
                        "Stop request sent to SkyNoid.";

                }

                else if (
                    command ===
                    "SET_MEDICINE_REMINDER"
                ) {

                    status.innerText =
                        "Medicine reminder sent to SkyNoid.";

                }

                else if (
                    command === "DIRECTION"
                ) {

                    status.innerText =
                        "Direction request sent to SkyNoid.";

                }

                else {

                    status.innerText =
                        "Request sent to SkyNoid.";

                }


                return true;

            }

            catch (error) {

                status.innerText =
                    "Unable to connect to SkyNoid.";

                return false;

            }
        }


        // Initialize conditional form fields.

        repeatChanged();

    </script>

</body>

</html>
"""


# ============================================================
# PHONE CALENDAR DOWNLOAD
# ============================================================

def escape_ics_text(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\r", "")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def safe_calendar_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_")
    return cleaned or "SkyNoid_Medicine_Reminder"


@app.get("/calendar")
def download_calendar(
    person: str,
    medicine: str,
    time: str,
    repeat: str = "once",
    date: str = "",
    instruction: str = "",
    selected_days: str = ""
):
    person = person.strip()
    medicine = medicine.strip()
    instruction = instruction.strip()
    repeat = repeat.strip().lower()
    date = date.strip()

    if not person:
        raise HTTPException(status_code=400, detail="Person name is required")
    if not medicine:
        raise HTTPException(status_code=400, detail="Medicine name is required")

    try:
        hour_text, minute_text = time.split(":")
        hour, minute = int(hour_text), int(minute_text)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid medicine time")

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise HTTPException(status_code=400, detail="Invalid medicine time")
    if repeat not in ALLOWED_REPEAT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid repeat option")

    day_codes = {
        "monday": "MO", "tuesday": "TU", "wednesday": "WE",
        "thursday": "TH", "friday": "FR", "saturday": "SA",
        "sunday": "SU"
    }
    weekday_numbers = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5,
        "sunday": 6
    }
    chosen_days = [
        x.strip().lower() for x in selected_days.split(",") if x.strip()
    ]

    if repeat == "selected":
        if not chosen_days:
            raise HTTPException(status_code=400, detail="Select at least one day")
        if any(day not in ALLOWED_DAYS for day in chosen_days):
            raise HTTPException(status_code=400, detail="Invalid selected day")

    now = datetime.now()

    if repeat == "once":
        if not date:
            raise HTTPException(status_code=400, detail="Medicine date is required")
        try:
            start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid medicine date")
    else:
        base = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        allowed = None
        if repeat == "weekdays":
            allowed = {0, 1, 2, 3, 4}
        elif repeat == "selected":
            allowed = {weekday_numbers[d] for d in chosen_days}

        start = None
        for offset in range(15):
            candidate = base + timedelta(days=offset)
            if candidate <= now:
                continue
            if allowed is None or candidate.weekday() in allowed:
                start = candidate
                break
        if start is None:
            raise HTTPException(
                status_code=400,
                detail="Unable to determine calendar date"
            )

    end = start + timedelta(minutes=15)
    description = f"Medicine reminder for {person}."
    if instruction:
        description += f" {instruction}."

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SkyNova Drones//SkyNoid//EN",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}@skynoid",
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{escape_ics_text('Medicine: ' + medicine)}",
        f"DESCRIPTION:{escape_ics_text(description)}",
    ]

    if repeat == "daily":
        lines.append("RRULE:FREQ=DAILY")
    elif repeat == "weekdays":
        lines.append("RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR")
    elif repeat == "selected":
        lines.append(
            "RRULE:FREQ=WEEKLY;BYDAY="
            + ",".join(day_codes[d] for d in chosen_days)
        )

    lines.extend([
        "BEGIN:VALARM",
        "TRIGGER:-PT10M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{escape_ics_text('Medicine reminder: ' + medicine)}",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ])

    calendar_text = "\r\n".join(lines) + "\r\n"
    filename = safe_calendar_filename(
        f"SkyNoid_{medicine}_Reminder"
    ) + ".ics"

    return Response(
        content=calendar_text,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# ============================================================
# PUBLIC COMMAND SUBMISSION
# ============================================================

@app.post("/command")
def submit_command(
    request: CommandRequest
):

    command = (
        request.command
        .strip()
        .upper()
    )

    payload = (
        request.payload
        or {}
    )


    # --------------------------------------------------------
    # VALID COMMAND
    # --------------------------------------------------------

    if command not in ALLOWED_COMMANDS:

        raise HTTPException(
            status_code=400,
            detail="Invalid SkyNoid command"
        )


    # --------------------------------------------------------
    # PLAY SONG
    # --------------------------------------------------------

    if command == "PLAY_SONG":

        song = str(
            payload.get(
                "song",
                ""
            )
        ).strip().upper()


        if song not in ALLOWED_SONGS:

            raise HTTPException(
                status_code=400,
                detail="Invalid SkyNoid song"
            )


        payload = {
            "song": song
        }


    # --------------------------------------------------------
    # STOP MUSIC
    # --------------------------------------------------------

    elif command == "STOP_MUSIC":

        payload = {}


    # --------------------------------------------------------
    # MEDICINE REMINDER
    # --------------------------------------------------------

    elif command == "SET_MEDICINE_REMINDER":

        person = str(
            payload.get(
                "person",
                ""
            )
        ).strip()


        medicine = str(
            payload.get(
                "medicine",
                ""
            )
        ).strip()


        instruction = str(
            payload.get(
                "instruction",
                ""
            )
        ).strip()


        time_text = str(
            payload.get(
                "time",
                ""
            )
        ).strip()


        repeat = str(
            payload.get(
                "repeat",
                "once"
            )
        ).strip().lower()


        date_text = payload.get(
            "date"
        )


        selected_days = payload.get(
            "selected_days",
            []
        )


        if not person:

            raise HTTPException(
                status_code=400,
                detail="Person name is required"
            )


        if not medicine:

            raise HTTPException(
                status_code=400,
                detail="Medicine name is required"
            )


        # Basic HH:MM validation.

        try:

            hour_text, minute_text = (
                time_text.split(":")
            )

            hour = int(
                hour_text
            )

            minute = int(
                minute_text
            )

        except (
            ValueError,
            AttributeError
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid medicine time"
            )


        if (
            hour < 0
            or hour > 23
            or minute < 0
            or minute > 59
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid medicine time"
            )


        if repeat not in ALLOWED_REPEAT_TYPES:

            raise HTTPException(
                status_code=400,
                detail="Invalid repeat option"
            )


        if repeat == "once":

            if not date_text:

                raise HTTPException(
                    status_code=400,
                    detail="Medicine date is required"
                )


            try:

                datetime.strptime(
                    str(date_text),
                    "%Y-%m-%d"
                )

            except ValueError:

                raise HTTPException(
                    status_code=400,
                    detail="Invalid medicine date"
                )


        else:

            date_text = None


        if repeat == "selected":

            if not isinstance(
                selected_days,
                list
            ):

                raise HTTPException(
                    status_code=400,
                    detail="Invalid selected days"
                )


            cleaned_days = []


            for day in selected_days:

                clean_day = (
                    str(day)
                    .strip()
                    .lower()
                )


                if clean_day not in ALLOWED_DAYS:

                    raise HTTPException(
                        status_code=400,
                        detail="Invalid selected day"
                    )


                if clean_day not in cleaned_days:

                    cleaned_days.append(
                        clean_day
                    )


            if not cleaned_days:

                raise HTTPException(
                    status_code=400,
                    detail="Select at least one day"
                )


            selected_days = cleaned_days


        else:

            selected_days = []


        payload = {

            "person":
                person,

            "medicine":
                medicine,

            "instruction":
                instruction,

            "time":
                time_text,

            "repeat":
                repeat,

            "date":
                date_text,

            "selected_days":
                selected_days
        }


    # --------------------------------------------------------
    # DIRECTION GUIDANCE
    # --------------------------------------------------------

    elif command == "DIRECTION":

        destination = str(
            payload.get(
                "destination",
                ""
            )
        ).strip().lower()

        allowed_destinations = {
            "director office",
            "balcony",
            "washroom",
        }

        if destination not in allowed_destinations:

            raise HTTPException(
                status_code=400,
                detail="Invalid SkyNoid destination"
            )

        payload = {
            "destination": destination
        }


    # --------------------------------------------------------
    # OLD COMMANDS
    # --------------------------------------------------------

    else:

        payload = {}


    # --------------------------------------------------------
    # CREATE COMMAND
    # --------------------------------------------------------

    command_id = str(
        uuid.uuid4()
    )


    item = {

        "id":
            command_id,

        "command":
            command,

        "payload":
            payload,

        "status":
            "pending",

        "created_at":
            datetime.utcnow().isoformat()
    }


    command_queue.append(
        item
    )

    command_history[
        command_id
    ] = item


    print(
        f"[QUEUE] Added: "
        f"{command} | "
        f"{command_id}"
    )


    if payload:

        print(
            f"[QUEUE] Payload: "
            f"{payload}"
        )


    return {

        "success":
            True,

        "id":
            command_id,

        "command":
            command,

        "payload":
            payload,

        "status":
            "pending"
    }


# ============================================================
# ROBOT GETS NEXT COMMAND
# ============================================================

@app.get("/robot/command")
def get_robot_command(
    authorization:
        str | None
        = Header(default=None)
):

    authenticate_robot(
        authorization
    )


    if not command_queue:

        return {
            "command": None
        }


    item = (
        command_queue.popleft()
    )


    item["status"] = (
        "processing"
    )

    item["processing_at"] = (
        datetime.utcnow().isoformat()
    )


    command_history[
        item["id"]
    ] = item


    print(
        f"[ROBOT] Sending: "
        f"{item['command']} | "
        f"{item['id']}"
    )


    if item.get(
        "payload"
    ):

        print(
            f"[ROBOT] Payload: "
            f"{item['payload']}"
        )


    return {

        "id":
            item["id"],

        "command":
            item["command"],

        "payload":
            item.get(
                "payload",
                {}
            ),

        "status":
            item["status"]
    }


# ============================================================
# ROBOT ACKNOWLEDGES COMMAND
# ============================================================

@app.post(
    "/robot/ack/{command_id}"
)
def acknowledge_command(
    command_id: str,
    authorization:
        str | None
        = Header(default=None)
):

    authenticate_robot(
        authorization
    )


    if (
        command_id
        not in command_history
    ):

        raise HTTPException(
            status_code=404,
            detail="Command not found"
        )


    item = (
        command_history[
            command_id
        ]
    )


    item["status"] = (
        "completed"
    )

    item["completed_at"] = (
        datetime.utcnow().isoformat()
    )


    command_history[
        command_id
    ] = item


    print(
        f"[ACK] Completed: "
        f"{item['command']} | "
        f"{command_id}"
    )


    return {

        "success":
            True,

        "id":
            command_id,

        "status":
            "completed"
    }


# ============================================================
# COMMAND STATUS
# ============================================================

@app.get(
    "/command/{command_id}"
)
def command_status(
    command_id: str
):

    if (
        command_id
        not in command_history
    ):

        raise HTTPException(
            status_code=404,
            detail="Command not found"
        )


    return command_history[
        command_id
    ]


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "online",

        "robot":
            ROBOT_ID,

        "queue_length":
            len(
                command_queue
            ),

        "available_commands":
            len(
                ALLOWED_COMMANDS
            ),

        "version":
            "2.2",

        "medicine_reminders":
            True
    }
