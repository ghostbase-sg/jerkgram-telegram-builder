from pathlib import Path
from jg131_final_stages import apply_final_stages
if __name__ == '__main__':
    apply_final_stages(Path(__file__).resolve().parents[1] / 'work/swiftgram-src')
    print('Build170 final stages applied; not compiled')
