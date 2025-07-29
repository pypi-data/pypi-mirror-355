import torchaudio
import torch
from glap import (
    glap_inference,
)


glap_inference.encode_text(['My name is candy'])

# glap = glap_inference()
# # glap = glap()

# glap = glap.eval()

# audio, sr = torchaudio.load('./resources/zero_caf9fceb_nohash_0.wav')

# text = ['The sound of silence','the sound of a car',"The sound of a child", "somebody is speaking","Quiet", "Es ist ruhig", "静音","Zero","0"]


# with torch.no_grad():
# scores = glap.score_forward(audio=audio, text=text)
# print(scores)


glap_model = glap_inference()
audio = torch.randn(1, 64000).tanh()
prefix = "The sound of"
labels = [
    f"{prefix} {label}"
    for label in (
        "Cat",
        "Dog",
        "Water",
        "Noise",
        "噪声",
    )
]
text_embeds = glap_model.encode_text(labels)
audio_embeds = glap_model.encode_audio(audio)
scores = glap_model.score(
    audio_embeds,
    text_embeds,
).squeeze(0)
for (
    label_name,
    score,
) in zip(
    labels,
    scores,
):
    print(f"{label_name} : {score.item()}")
