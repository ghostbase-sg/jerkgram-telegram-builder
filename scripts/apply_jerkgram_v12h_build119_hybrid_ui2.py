#!/usr/bin/env python3

from pathlib import Path
import importlib.util


BASE = Path(__file__).resolve().with_name("apply_jerkgram_v12h_build119_hybrid_ui1.py")


def load_base():
    spec = importlib.util.spec_from_file_location("jerkgram_build119_hybrid_ui1", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("[Build119 hybrid UI2] unable to load Build119 UI1")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    module = load_base()

    def patch_about(text):
        start, end = module.block_bounds(text, "if page == .about {")
        block = text[start:end]
        module.require(
            "BUILD118_ABOUT_CHANNEL_CARDS1" in block,
            "Build118 About cards prerequisite missing",
        )
        old_footer = '.info(1, "Jerkgram\\nBase: Official Telegram 12.9.2\\nBuild: 118")'
        module.require(
            block.count(old_footer) == 1,
            "Build118 About footer exact owner count != 1",
        )
        block = block.replace(
            old_footer,
            ".info(1, strings.aboutBuild119Summary)",
            1,
        )
        return text[:start] + block + text[end:]

    module.patch_about = patch_about
    module.main()
    print("[Build119 hybrid UI2] exact Build118 About footer -> Build119 semantic identity")


if __name__ == "__main__":
    main()
