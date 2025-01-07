import whisper
import argparse
import glob
import pandas as pd

# python3 transcriptions.py -L Fr
# Pour transcrire les textes du français !

def get_audio_files(folder):
   
    audio_files = glob.glob(f"{folder}/*.mp3")
    return audio_files

def load_stt_model(model_name):
  
    model = whisper.load_model(model_name)
    return model

def transcription(model, audio_file):
    
    result = model.transcribe(audio_file)
    text = result["text"]
    return text

def insert_column(csv_table, transcriptions, audio_files):

    df = pd.read_csv(csv_table)

    for audio_file, transcription in zip(audio_files, transcriptions):
        file_name = audio_file.split("/")[-1]

        df.loc[df["File Name"] == file_name, "Transcription"] = transcription

    return df

def main():
   
    languages = ["Fr", "En", "De", "Es", "It", "Ru", "Po", "Ch", "Oc", "Ar", "Ca", "Co", "Cr", "He"]
    parser = argparse.ArgumentParser(description='Scrap la langue désirée.')
    parser.add_argument("-L", "--Langue", required=True, choices=languages,
                        help="""Fr = Français, En = Anglais, De = Allemand, Es = Espagnol, It = Italien, Ru = Russe, Po = Portugais, Ch = Chinois,
                        Oc = Occitan, Ar = Arabe, Ca = Catalan, Co = Corse, Cr = Créole, He = Hébreu.""")
    args = parser.parse_args()

    audio_files = get_audio_files(f"../data/audios/{args.Langue}")

    model = load_stt_model("tiny")

    transcriptions = [transcription(model, audio_file) for audio_file in audio_files]

    df = insert_column(f"../data/tables/{args.Langue}.csv", transcriptions, audio_files)

    df.to_csv(f"../data/tables/{args.Langue}_transcriptions.csv", index=False)

if __name__ == "__main__":
    main()
