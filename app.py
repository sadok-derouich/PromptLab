from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CONFIG_PATH = "config.json"
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError("Missing config.json with your API keys and DB config.")

with open(CONFIG_PATH) as f:
    config = json.load(f)

OPENAI_API_KEY = config.get("OPENAI_API_KEY")
DEEPSEEK_API_KEY = config.get("DEEPSEEK_API_KEY")
DB_HOST = config.get("DB_HOST")
DB_NAME = config.get("DB_NAME")
DB_USER = config.get("DB_USER")
DB_PASS = config.get("DB_PASS")

if not all([OPENAI_API_KEY, DEEPSEEK_API_KEY, DB_HOST, DB_NAME, DB_USER, DB_PASS]):
    raise ValueError("Missing keys or DB config in config.json")

def get_db_connection():
    return psycopg2.connect(
        host=config["DB_HOST"],
        database=config["DB_NAME"],
        user=config["DB_USER"],
        password=config["DB_PASS"],
        port=config.get("DB_PORT", 5432),
        sslmode="require",  # Supabase requires SSL
        cursor_factory=RealDictCursor
    )


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

@app.route("/list-prompts/<prompt_type>")
def list_prompts(prompt_type):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if prompt_type == "system":
            cur.execute("SELECT * FROM system_prompts")
        else:
            cur.execute("SELECT * FROM user_prompts")

        rows = cur.fetchall()
        conn.close()
        return jsonify(rows)

    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            conn.rollback()  # try to recover the connection
            conn.close()
        except:
            pass
        return jsonify({"error": str(e)}), 500


@app.route("/load-prompt/<prompt_type>/<prompt_id>")
def load_prompt(prompt_type, prompt_id):
    conn = get_db_connection()
    cur = conn.cursor()
    table = "system_prompts" if prompt_type == "system" else "user_prompts"
    cur.execute(f"SELECT * FROM {table} WHERE id = %s", (prompt_id,))
    row = cur.fetchone()
    conn.close()
    return jsonify(row) if row else jsonify({"error": "Prompt not found"}), 404

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

    if prompt_type == "system":
        if mode == "edit":
            cur.execute("SELECT id FROM system_prompts WHERE name = %s AND version = %s AND id != %s", (name, version, id))
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "Another system prompt with this name and version already exists."})
            cur.execute("""
                UPDATE system_prompts
                SET name = %s, version = %s, content = %s, last_update = %s, comment = %s
                WHERE id = %s
            """, (name, version, content, now, comment, id))
        else:
            cur.execute("SELECT id FROM system_prompts WHERE name = %s AND version = %s", (name, version))
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "System prompt with this name and version already exists."})
            cur.execute("""
                INSERT INTO system_prompts (name, version, content, creation_date, last_update, comment)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, version, content, now, now, comment))

    else:
        if mode == "edit":
            cur.execute("SELECT id FROM user_prompts WHERE name = %s AND version = %s AND id != %s", (name, version, id))
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "Another user prompt with this name and version already exists."})
            cur.execute("""
                UPDATE user_prompts
                SET name = %s, version = %s, content = %s, comment = %s
                WHERE id = %s
            """, (name, version, content, comment, id))
        else:
            cur.execute("SELECT id FROM user_prompts WHERE name = %s AND version = %s", (name, version))
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "User prompt with this name and version already exists."})
            cur.execute("""
                INSERT INTO user_prompts (name, version, content, creation_date, comment)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, version, content, now, comment))

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
        if provider == "openai":
            from openai import OpenAI as OpenAIClient
            client = OpenAIClient(api_key=OPENAI_API_KEY)
        elif provider == "deepseek":
            from openai import OpenAI
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        else:
            return jsonify({"error": "Invalid provider"}), 400

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

@app.route("/save-output", methods=["POST"])
def save_output():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO outputs (system_id, user_id, api, model, temperature, response_time, response, ranking)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("system_id"),
        data.get("user_id"),
        data.get("api"),
        data.get("model"),
        data.get("temperature"),
        data.get("response_time"),
        data.get("response"),
        data.get("ranking")
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
        SELECT o.id, o.api, o.model, o.temperature, o.response_time, o.ranking, o.response, o.created_at,
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

if __name__ == "__main__":
    app.run(debug=True, port=5001)
