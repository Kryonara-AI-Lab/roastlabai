import os
import json
import re
from flask import Blueprint, render_template, request, send_from_directory
import requests

bp = Blueprint('routes', __name__)

def extract_valid_json(raw_response):
    """
    Cleans raw AI response text of markdown wrappers (```json ... ```) 
    and handles common decoding snags cleanly.
    """
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)

@bp.route('/', methods=['GET', 'POST'])
def index():
    roast_result = None
    user_input = ""
    selected_intensity = "Savage"
    selected_personality = "Tech Bro"

    if request.method == 'POST':
        user_input = request.form.get('user_input', '')
        selected_intensity = request.form.get('intensity', 'Savage')
        selected_personality = request.form.get('personality', 'Tech Bro')

        if user_input.strip():
            system_prompt = (
                "You are a master roast AI in a premium brutalist editorial startup review system. "
                f"Persona: '{selected_personality}'. Intensity: '{selected_intensity}'. "
                "You must evaluate the user's input and reply ONLY with a raw valid JSON object. "
                "Do not include any markdown tags, markdown blocks, backticks, or wrappers in your reply. "
                "The response must be pure JSON containing these exact keys:\n"
                "1. 'headline': Short, devastating editorial hook quotes summarizing the project flaws.\n"
                "2. 'score': An integer rating out of 100 based on execution quality.\n"
                "3. 'roast_bullets': An array containing exactly 5 quick, sharp, witty punchlines mapping critical flaws.\n"
                "4. 'brutal_truth': A paragraph detailing why the market segment or mechanics won't survive long term.\n"
                "5. 'worth_saving': A concise positive or pivot observation pointing out what tiny aspect actually holds value.\n"
                "6. 'eats_lunch': Mentioning direct alternatives or behavioral habits that render this redundant.\n"
                "7. 'one_move': The strategic pivot or immediate development choice they should make right now."
            )

            api_key = os.getenv("OPENROUTER_API_KEY")

            if api_key:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://127.0.0.1:5000", 
                    "X-Title": "RoastLab AI"
                }
                payload = {
                    "model": "openrouter/free", 
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ]
                }

                try:
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions", 
                        json=payload, 
                        headers=headers,
                        timeout=30
                    )
                    if response.status_code == 200:
                        raw_content = response.json()['choices'][0]['message']['content']
                        roast_result = extract_valid_json(raw_content)
                    else:
                        roast_result = {
                            "headline": "Server Exhaustion Fault", 
                            "score": 0, 
                            "roast_bullets": [f"API returned status code: {response.status_code}"], 
                            "brutal_truth": "OpenRouter free pool is currently overloaded. Please retry in a few seconds.", 
                            "worth_saving": "Your concept is fine, the server network routing is the issue here.", 
                            "eats_lunch": "System limits.", 
                            "one_move": "Hit the 'Roast My Idea' button once more."
                        }
                except Exception as e:
                    roast_result = {
                        "headline": "Connection Fault", 
                        "score": 0, 
                        "roast_bullets": [str(e)], 
                        "brutal_truth": "Failed to sync with OpenRouter servers.", 
                        "worth_saving": "None.", 
                        "eats_lunch": "Connection timeouts.", 
                        "one_move": "Restart your Flask development terminal."
                    }
            else:
                roast_result = {
                    "headline": "Substack for ADHD-addled attention spans",
                    "score": 15,
                    "roast_bullets": [
                        "Seven seconds? That's barely enough time to clear your throat.",
                        "So, just a series of rapid-fire audible shrugs?",
                        "Perfect for people who want less content, but somehow more annoying.",
                        "Is 'ums' and 'uhs' the new content goto?",
                        "Finally, a podcast for your housefly!"
                    ],
                    "brutal_truth": "You're trying to inject a format constraint (7 seconds) into a platform (Substack) built for depth, analysis, and narrative. Content creators generally want more space, not less, to convey value.",
                    "worth_saving": "The fundamental desire to create and consume audio content easily is valid, and voice notes via social media have unexplored potential outside standard podcasts.",
                    "eats_lunch": "TikTok, Instagram Reels, and existing podcast platforms where creators already post truncated voice clips or threads.",
                    "one_move": "Pivot from '7 seconds' to short-form narrative audio channels (1-3 minutes) focused on concise storytelling instead of simple soundbites."
                }

    return render_template(
        'index.html', 
        roast_result=roast_result, 
        user_input=user_input,
        selected_intensity=selected_intensity,
        selected_personality=selected_personality
    )

@bp.route('/favicon.ico')
def favicon():
    # Quiet the 404 errors on direct favicon requests from browsers
    return send_from_directory(os.path.join(bp.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Support direct template renderings
@bp.route('/privacy.html')
@bp.route('/compliance/privacy')
def privacy():
    return render_template('privacy.html')

@bp.route('/terms.html')
@bp.route('/compliance/terms')
def terms():
    return render_template('terms.html')

@bp.route('/DCL.html')
@bp.route('/compliance/cryptography')
def cryptography():
    return render_template('DCL.html')

@bp.route('/Model.html')
@bp.route('/compliance/parameters')
def parameters():
    return render_template('Model.html')

@bp.route('/company/manifesto')
@bp.route('/manifesto.html')
def manifesto():
    return render_template('manifesto.html')

@bp.route('/company/pricing')
@bp.route('/enterprise.html')
def pricing():
    return render_template('enterprise.html')

@bp.route('/company/protocol')
@bp.route('/TAP.html')
def protocol():
    return render_template('TAP.html')

@bp.route('/company/logs')
@bp.route('/engin_log.html')
def logs():
    return render_template('engin_log.html')