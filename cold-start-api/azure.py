# azure.py

import pandas as pd

def predict_azure(model, avg, spread, ratio, memory, mem_spread):

    input_data = pd.DataFrame([{
        "Average": avg,
        "duration_spread": spread,
        "p99_p50_ratio": ratio,
        "AverageAllocatedMb": memory,
        "memory_spread": mem_spread
    }])

    prob = model.predict_proba(input_data)[0][1]

    return prob