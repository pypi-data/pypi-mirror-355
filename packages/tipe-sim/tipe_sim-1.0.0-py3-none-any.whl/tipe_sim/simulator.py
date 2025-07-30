# tipe_sim/simulator.py
# FINAL VERSION FOR PERSONAL USE - CONTAINS HARD-CODED API KEY
# This module contains the core logic for generating the simulation.
import requests
import json
import os

def generate_simulation(sujet: str, output_path: str = "simulation.html"):
    """
    Generates an HTML/CSS/JS simulation based on a TIPE topic using the Gemini API.

    Args:
        sujet (str): The TIPE topic for the simulation.
        output_path (str): The path to save the generated HTML file.

    Returns:
        The HTML content of the simulation as a string, or None on failure.
    """
    # --- SECURITY WARNING: Do NOT publish a library with a hard-coded API key. ---
    API_KEY = "AIzaSyBRCY59APTg8JEKRHFngisylhTpOSm039I"

    if not sujet:
        raise ValueError("TIPE 'sujet' (topic) cannot be empty.")

    prompt_template = """
    You are a world-class simulation designer and scientific visualizer with an obsessive attention to detail, tasked with creating a flawless, presentation-ready tool for a French TIPE CPGE project.

    **PRIMARY DIRECTIVE: VISUALIZATION IS EVERYTHING.**
    Your goal is to create a PURELY VISUAL simulation. Do NOT include panels with long text explanations of the scientific model. The simulation itself must be the explanation.
    You must deeply analyze the scientific principles of the provided topic: "{user_sujet}". The design MUST be a direct and insightful consequence of this analysis.

    **PHASE 2: FLAWLESS EXECUTION**
    Based on your analysis, generate a single, complete HTML file. This is a "hyper-designed" piece of academic software.

    **CRITICAL REQUIREMENTS:**

    1.  **Language:** All user-facing text (titles, labels, buttons) MUST be in **French**.
    2.  **Design and Aesthetics:**
        - **Hyper-Design:** The visual design must be stunning, modern, and professional. Use Tailwind CSS to create a clean, dark-themed dashboard. Layout, typography, and spacing must be impeccable.
        - **Purposeful Animation:** If the topic requires animation (on an HTML Canvas), it must be smooth, physically accurate, and the central focus of the page.
    3.  **Scientific Charting Excellence:**
        - **This is a non-negotiable, critical requirement.** If charts are appropriate, they must be scientifically correct and visually perfect.
        - For diagrams plotting one variable against another (e.g., a P-V diagram for thermodynamics, a phase portrait), you MUST structure the Chart.js data as an array of objects: `data: [{x: pressure1, y: volume1}, {x: pressure2, y: volume2}, ...]`.
        - A simple array `[value1, value2, ...]` is UNACCEPTABLE for such plots. The chart's axes must be clearly labeled with the correct physical quantities and units.
    4.  **Academic and Technical Rigor:**
        - **Perfect LaTeX (If Needed):** If you present any equations on the dashboard, they must be rendered perfectly with KaTeX. EVERY backslash `\` MUST be escaped to `\\\\`.
        - **Intelligent Tool Selection:** You have full autonomy to select the best tools (Canvas, Chart.js, Three.js) from a CDN.
        - **Rock-Solid Interactivity:** The simulation must start with a "Démarrer" button.
        - **Impeccable Code:** The final HTML file must contain heavily commented, clean, and organized code.

    Now, execute your directive. Begin by understanding "{user_sujet}" and then create the ultimate, flawless, and PURELY VISUAL simulation for it in French.
    """

    prompt = prompt_template.replace("{user_sujet}", sujet)

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    print("Sending request to Gemini API for a Flawless, Hyper-Designed Simulation...")

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_json = response.json()

        generated_text = response_json['candidates'][0]['content']['parts'][0]['text']

        if "```html" in generated_text:
            html_content = generated_text.split("```html", 1)[1].split("```")[0].strip()
        else:
            html_content = generated_text.strip()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Professional simulation successfully generated and saved to: {os.path.abspath(output_path)}")
        return html_content

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the Gemini API: {e}")
        return None
    except (KeyError, IndexError):
        print("Could not parse the response from the API. The response may be empty or malformed.")
        return None
