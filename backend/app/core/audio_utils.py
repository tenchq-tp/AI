import os
from pydub import AudioSegment

def split_and_convert_audio(mp3_path: str, output_dir: str, base_filename: str):
    audio = AudioSegment.from_file(mp3_path, format="mp3") # โหลดไฟล์ MP3

    if audio.channels != 2: # เช็คว่าเป็น Stereo ไหม
        raise ValueError("Input audio must be stereo (2 channels)")

    # แยก Channel
    channels = audio.split_to_mono()
    agent = channels[0]  # L = agent
    customer = channels[1] # R = customer

    # ปรับ sample rate เป็น 16,000 Hz # set_channels(1) → แปลงให้เป็น mono (1 channel)
    agent = agent.set_frame_rate(16000).set_channels(1)
    customer = customer.set_frame_rate(16000).set_channels(1)

    os.makedirs(output_dir, exist_ok=True) # สร้างโฟลเดอร์

    agent_path = os.path.join(output_dir, f"{base_filename}_agent.wav")
    customer_path = os.path.join(output_dir, f"{base_filename}_customer.wav")

    agent.export(agent_path, format="wav")
    customer.export(customer_path, format="wav")

    return agent_path, customer_path
