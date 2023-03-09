import openai
import pytube
import whisper
from flask import Flask, render_template, request

openai.api_key = "xxxxx"

app = Flask(__name__)


class Transcribe:
    def __init__(self, video_link="", filename="sample-file.mp4"):
        self.video_link = video_link
        self.filename = filename

    def convert_video_to_audio(self):
        """Converts YouTube video to audio mp4"""
        if not self.video_link.strip():
            raise ValueError("No video link found")

        try:
            data = pytube.YouTube(self.video_link)
            st = data.streams.get_by_itag(139)
            st.download("", self.filename)
        except pytube.exceptions.VideoUnavailable:
            raise ValueError("The specified video is unavailable")
        except pytube.exceptions.RegexMatchError:
            raise ValueError("Invalid YouTube link provided")
        except pytube.exceptions.ExtractError:
            raise ValueError("Error extracting YouTube video information")

    def convert_audio_to_text(self):
        """Converts audio to transcript text using Whisper"""
        model = whisper.load_model("base")
        text = model.transcribe(self.filename)
        return text["text"]

    def prepare_prompt(self, prompt_type, input_text, summary_length=0):
        """Prepares a prompt for OpenAI GPT-3"""
        if prompt_type not in ["highlight", "summary"]:
            raise ValueError("Invalid prompt type selected")

        if prompt_type == "highlight":
            prompt_text = f"Get highlights of the following text: {input_text}"
        elif prompt_type == "summary":
            if summary_length:
                prompt_text = f"Summarize this text in {summary_length} words or fewer: {input_text}"
            else:
                prompt_text = f"Summarize this text: {input_text}"

        return {"success": True, "prompt_text": prompt_text}

    def get_summary(self):
        """Converts video to audio, transcribes to text, generates a summary using OpenAI GPT-3"""
        try:
            self.convert_video_to_audio()
            text = self.convert_audio_to_text()
            prompt = self.prepare_prompt("highlight", text)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt["prompt_text"]}],
            )
            summary = response.choices[0].message.content
            return {"success": True, "summary": summary.strip()}
        except ValueError as e:
            return {"success": False, "msg": str(e)}
        except Exception as e:
            return {"success": False, "msg": "Error generating summary", "error": str(e)}


@app.route('/', methods=['GET', 'POST'])
def index():
    errors, url = "", ""
    results = {}
    if request.method == "POST":
        try:
            url = request.form['video_url']
            transcript_obj = Transcribe(url)
            results = transcript_obj.get_summary()
            print(results)
        except:
            errors = "Unable to get URL. Please make sure it's valid and try again."
    return render_template('index.html', error=errors, summary=results.get("summary", {}), video_url=url)
