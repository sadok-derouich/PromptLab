from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from datetime import datetime
from io import StringIO
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
import json
import csv

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Load config.json (must exist)
CONFIG_PATH = "config.json"
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError("Missing config.json with your API keys and DB config.")

with open(CONFIG_PATH) as f:
    config = json.load(f)

# Extract keys and DB credentials
OPENAI_API_KEY = config.get("OPENAI_API_KEY")
DEEPSEEK_API_KEY = config.get("DEEPSEEK_API_KEY")
DB_HOST = config.get("DB_HOST")
DB_NAME = config.get("DB_NAME")
DB_USER = config.get("DB_USER")
DB_PASS = config.get("DB_PASS")
DB_PORT = config.get("DB_PORT", 5432)

if not all([OPENAI_API_KEY, DEEPSEEK_API_KEY, DB_HOST, DB_NAME, DB_USER, DB_PASS]):
    raise ValueError("Missing keys or DB config in config.json")

# PostgreSQL DB connection
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        sslmode="require",  # Supabase requires SSL
        cursor_factory=RealDictCursor
    )

# ----------- Static HTML Serving -----------

@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/prompt-runner.html")
def serve_runner():
    return send_from_directory(".", "prompt-runner.html")

@app.route("/prompt-admin.html")
def serve_admin():
    return send_from_directory(".", "prompt-admin.html")

@app.route("/outputs.html")
def serve_outputs():
    return send_from_directory(".", "outputs.html")

# ----------- Prompt Management (CRUD) -----------

@app.route("/list-prompts/<prompt_type>")
def list_prompts(prompt_type):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        table = "system_prompts" if prompt_type == "system" else "user_prompts"
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/load-prompt/<prompt_type>/<prompt_id>")
def load_prompt(prompt_type, prompt_id):
    conn = get_db_connection()
    cur = conn.cursor()
    table = "system_prompts" if prompt_type == "system" else "user_prompts"
    cur.execute(f"SELECT * FROM {table} WHERE id = %s", (prompt_id,))
    row = cur.fetchone()
    conn.close()
    return jsonify(row) if row else (jsonify({"error": "Prompt not found"}), 404)

@app.route("/admin/update", methods=["POST"])
def update_prompt():
    data = request.get_json()
    prompt_type = data.get("type")
    mode = data.get("mode")
    id = data.get("id")
    name = data.get("name")
    version = data.get("version", "1.0.0")
    content = data.get("content")
    comment = data.get("comment")
    now = datetime.now()

    conn = get_db_connection()
    cur = conn.cursor()

    table = "system_prompts" if prompt_type == "system" else "user_prompts"

    if mode == "edit":
        # Ensure uniqueness of name+version except current
        cur.execute(f"SELECT id FROM {table} WHERE name = %s AND version = %s AND id != %s", (name, version, id))
        if cur.fetchone():
            conn.close()
            return jsonify({"error": f"Another {prompt_type} prompt with this name and version already exists."})
        cur.execute(f"""
            UPDATE {table}
            SET name = %s, version = %s, content = %s,
                last_update = %s, comment = %s
            WHERE id = %s
        """, (name, version, content, now if prompt_type == "system" else None, comment, id))
    else:
        # New prompt (or new version)
        cur.execute(f"SELECT id FROM {table} WHERE name = %s AND version = %s", (name, version))
        if cur.fetchone():
            conn.close()
            return jsonify({"error": f"{prompt_type.capitalize()} prompt with this name and version already exists."})
        fields = "(name, version, content, creation_date, comment" + (", last_update" if prompt_type == "system" else "") + ")"
        values = "%s, %s, %s, %s, %s" + (", %s" if prompt_type == "system" else "")
        params = [name, version, content, now, comment]
        if prompt_type == "system":
            params.append(now)
        cur.execute(f"INSERT INTO {table} {fields} VALUES ({values})", params)

    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route("/admin/delete/<prompt_type>/<int:prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_type, prompt_id):
    conn = get_db_connection()
    cur = conn.cursor()
    table = "system_prompts" if prompt_type == "system" else "user_prompts"
    cur.execute(f"DELETE FROM {table} WHERE id = %s", (prompt_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

# ----------- Prompt Execution -----------

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    system_prompt = data.get("system_prompt", "")
    user_prompt = data.get("user_prompt", "")
    provider = data.get("provider", "deepseek")
    model = data.get("model", "deepseek-chat")
    temperature = data.get("temperature", 0.7)

    start = time.time()

    try:
        # Dynamic API client setup
        if provider == "openai":
            from openai import OpenAI as OpenAIClient
            client = OpenAIClient(api_key=OPENAI_API_KEY)
        elif provider == "deepseek":
            from openai import OpenAI
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        else:
            return jsonify({"error": "Invalid provider"}), 400

        # Run chat completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )

        content = response.choices[0].message.content
        duration = round(time.time() - start, 2)

        return jsonify({"response": content, "duration": duration})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------- Output Logging -----------

@app.route("/save-output", methods=["POST"])
def save_output():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO outputs (system_id, user_id, api, model, temperature,
                             response_time, response, ranking, comment)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("system_id"),
        data.get("user_id"),
        data.get("api"),
        data.get("model"),
        data.get("temperature"),
        data.get("response_time"),
        data.get("response"),
        data.get("ranking"),
        data.get("comment")
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

@app.route("/delete-output/<int:output_id>", methods=["DELETE"])
def delete_output(output_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM outputs WHERE id = %s", (output_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route("/outputs", methods=["GET"])
def get_outputs():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.api, o.model, o.temperature, o.response_time, o.ranking, o.response, o.comment, o.created_at,
               sp.id as system_id, sp.name as system_name, sp.version as system_version,
               up.id as user_id, up.name as user_name, up.version as user_version
        FROM outputs o
        LEFT JOIN system_prompts sp ON o.system_id = sp.id
        LEFT JOIN user_prompts up ON o.user_id = up.id
        ORDER BY o.created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/export-outputs.csv")
def export_outputs_csv():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            o.created_at, 
            sp.id AS system_id, sp.name AS system_name, sp.version AS system_version,
            up.id AS user_id, up.name AS user_name, up.version AS user_version,
            o.api, o.model, o.temperature, o.response_time, o.ranking, o.response, o.comment
        FROM outputs o
        LEFT JOIN system_prompts sp ON o.system_id = sp.id
        LEFT JOIN user_prompts up ON o.user_id = up.id
        ORDER BY o.created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date",
        "System prompt id", "System prompt name", "System prompt version",
        "User prompt id", "User prompt name", "User prompt version",
        "API", "Model", "Temperature", "Time", "Rank", "Response", "Output Comment"
    ])
    for row in rows:
        writer.writerow([
            row["created_at"],
            row["system_id"], row["system_name"], row["system_version"],
            row["user_id"], row["user_name"], row["user_version"],
            row["api"], row["model"], row["temperature"], row["response_time"], row["ranking"],
            row["response"], row["comment"]
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=outputs.csv"}
    )

# ----------- App Entry -----------

if __name__ == "__main__":
    app.run(debug=True, port=5001)
