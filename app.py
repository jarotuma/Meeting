import streamlit as st
import os
from groq import Groq
import google.generativeai as genai
from docx import Document
import io

# Nastavení vzhledu
st.set_page_config(page_title="Chytrý zápis ze schůzky", page_icon="📝", layout="centered")

st.title("📝 Generátor manažerských zápisů")
st.markdown("Nahraj audio ze schůzky a AI ti vygeneruje strukturovaný zápis ve Wordu.")

# Nahrání souboru
audio_file = st.file_uploader("Nahraj záznam ze schůzky (MP3, WAV, M4A)", type=['mp3', 'wav', 'm4a'])

if st.button("🚀 Vygenerovat zápis", use_container_width=True):
    if not audio_file:
        st.warning("Nejprve prosím nahraj soubor s audiem.")
    else:
        try:
            # Načtení klíčů z tajného trezoru
            groq_api_key = st.secrets["GROQ_API_KEY"]
            gemini_api_key = st.secrets["GEMINI_API_KEY"]

            # 1. PŘEPIS AUDIA
            with st.spinner("⏳ Poslouchám a přepisuji audio (může to chvilku trvat)..."):
                with open("temp_audio.mp3", "wb") as f:
                    f.write(audio_file.getbuffer())
                
                client = Groq(api_key=groq_api_key)
                with open("temp_audio.mp3", "rb") as file:
                    transcription = client.audio.transcriptions.create(
                      file=("temp_audio.mp3", file.read()),
                      model="whisper-large-v3",
                      response_format="text",
                      language="cs"
                    )
                os.remove("temp_audio.mp3")
            
            st.success("✅ Přepis byl úspěšně dokončen!")

            # 2. TVORBA ZÁPISU
            with st.spinner("⏳ Generuji manažerský zápis..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
                Jsi profesionální firemní asistent. Přečti si následující surový přepis ze schůzky a vytvoř z něj přehledný manažerský zápis v češtině.
                Rozděl ho na:
                1. Hlavní téma schůzky
                2. Nejdůležitější probrané body (odrážky)
                3. Učiněná rozhodnutí
                4. Akční kroky / Úkoly (Kdo má co udělat)
                
                Zde je přepis:
                {transcription}
                """
                response = model.generate_content(prompt)
                zapis_text = response.text
                
            st.success("✅ Zápis je hotový!")
            st.markdown("### Náhled zápisu:")
            st.write(zapis_text)

            # 3. TVORBA WORDU PRO STAŽENÍ
            doc = Document()
            doc.add_heading('Zápis ze schůzky', 0)
            doc.add_paragraph(zapis_text)
            
            bio = io.BytesIO()
            doc.save(bio)
            
            st.download_button(
                label="💾 Stáhnout zápis jako Word (.docx)",
                data=bio.getvalue(),
                file_name="zapis_ze_schuzky.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Ouvej, něco se pokazilo: {e}")
