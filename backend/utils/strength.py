from zxcvbn import zxcvbn

def check_strength(password: str) -> dict:
    result = zxcvbn(password)
    return {
        "score": result["score"],  # 0 (weak) → 4 (strong)
        "crack_time": result["crack_times_display"]["offline_fast_hashing_1e10_per_second"],
        "feedback": result["feedback"]
    }
