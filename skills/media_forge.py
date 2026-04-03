import ffmpeg
import re
import os

class MediaForgeSkill:
    def __init__(self):
        self.output_dir = "generated_code"
        print(">> Media Forge Skill: ONLINE (FFmpeg Active)")

    def _resolve_path(self, filename):
        """Checks if file exists in root or generated_code folder."""
        if os.path.exists(filename):
            return filename
        
        # Check in generated_code folder
        vault_path = os.path.join(self.output_dir, filename)
        if os.path.exists(vault_path):
            return vault_path
        
        return None

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()

            # --- 1. VIDEO TO AUDIO CONVERSION ---
            # Trigger: "convert [file.mp4] to mp3"
            video_match = re.search(r'convert\s+([\w\-. ]+\.\w+)\s+to\s+mp3', cmd)
            if video_match:
                filename = video_match.group(1).strip()
                input_path = self._resolve_path(filename)
                
                if not input_path:
                    return f"Sir, I could not find the file '{filename}' to convert."

                output_path = os.path.splitext(input_path)[0] + ".mp3"
                
                print(f">> [MediaForge] Converting {filename} to MP3...")
                try:
                    (
                        ffmpeg
                        .input(input_path)
                        .output(output_path, acodec='libmp3lame', ab='192k')
                        .overwrite_output()
                        .run(quiet=True)
                    )
                    return f"Sir, I have successfully extracted the audio to {os.path.basename(output_path)}."
                except Exception as e:
                    return f"Sir, the conversion failed due to an internal FFmpeg error."

            # --- 2. IMAGE RESIZING ---
            # Trigger: "resize [file.png] to [1080p/720p/etc]"
            resize_match = re.search(r'resize\s+([\w\-. ]+\.\w+)\s+to\s+(\d+p|\d+x\d+)', cmd)
            if resize_match:
                filename = resize_match.group(1).strip()
                res = resize_match.group(2).strip()
                input_path = self._resolve_path(filename)

                if not input_path:
                    return f"Sir, I cannot find '{filename}' to resize."

                res_map = {"1080p": "1920:1080", "720p": "1280:720", "480p": "854:480"}
                dims = res_map.get(res, res.replace('x', ':'))
                
                output_path = f"{os.path.splitext(input_path)[0]}_resized_{res}{os.path.splitext(input_path)[1]}"

                print(f">> [MediaForge] Resizing {filename} to {res}...")
                try:
                    w, h = dims.split(':')
                    (
                        ffmpeg
                        .input(input_path)
                        .filter('scale', w, h)
                        .output(output_path)
                        .overwrite_output()
                        .run(quiet=True)
                    )
                    return f"Sir, the image has been resized to {res} and saved as {os.path.basename(output_path)}."
                except Exception:
                    return f"Sir, I encountered an error while resizing the image."

            return None # Pass to next skill if no matches

        except Exception as e:
            print(f"[MediaForge Error] {e}")
            return None