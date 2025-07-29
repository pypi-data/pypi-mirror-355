import torch
import argparse
from glap_model import glap_inference


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_audio", help="Input Audio file")
    parser.add_argument("input_text", help="Input text, can be separated with ;")
    parser.add_argument("-d", "--dir", help="Input audios in a dir")
    args = parser.parse_args()
    run_inference(audio_path=args.input_audio, text=args.input_text)


def run_inference(
    audio_path: str,
    text: str,  # Should be split for multiple sentences using ;
):
    import torchaudio

    device_type = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_type)

    model = glap_inference()
    model = model.to(device).eval()
    audio, sr = torchaudio.load(audio_path)
    if sr != 16000:
        audio = torchaudio.functional.resample(audio, sr, 16000)
    if audio.shape[0] > 1:
        audio = audio.mean(0, keepdim=True)

    audio_length = torch.tensor(audio.shape[-1]).unsqueeze(0)

    def clapscore(audio_emb, text_emb):
        return (100 * (audio_emb @ text_emb.T)).squeeze(0)

    texts = text.split(";")
    with torch.inference_mode():
        model_inputs = dict(audio=audio, audio_length=audio_length)

        model_inputs = {k: v.to(device) for k, v in model_inputs.items()}
        # Text is still a list
        model_inputs["text"] = texts
        with torch.autocast(device_type=device_type, enabled=True):
            audio_embeds, text_embeds = model(**model_inputs)
        scores = clapscore(audio_embeds, text_embeds)
    for score, text in zip(scores, texts):
        print(f"{audio_path} [{text}] : {score:.2f}")
