#!/usr/bin/env python3
import torch
import torch.nn as nn
import time
import argparse
import sys

# === CLI ARGUMENTS ===
def parse_args():
    parser = argparse.ArgumentParser(description="LM Bench - LLM Training Capability Benchmark")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda", "mps"],
                        help="Device to use: auto, cpu, cuda, or mps")
    return parser.parse_args()

# === GET DEVICE ===
def get_device(choice):
    if choice == "auto":
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")
    else:
        if choice == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but not available.")
        if choice == "mps" and not torch.backends.mps.is_available():
            raise ValueError("MPS requested but not available.")
        return torch.device(choice)

# === Transformer Block ===
class TransformerBlock(nn.Module):
    def __init__(self, hidden_size, n_heads):
        super().__init__()
        self.attn = nn.MultiheadAttention(hidden_size, n_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(hidden_size)
        self.ff = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 4),
            nn.GELU(),
            nn.Linear(hidden_size * 4, hidden_size)
        )
        self.norm2 = nn.LayerNorm(hidden_size)

    def forward(self, x):
        attn_out, _ = self.attn(x, x, x)
        x = self.norm1(x + attn_out)
        x = self.norm2(x + self.ff(x))
        return x

# === Test Model ===
class TestModel(nn.Module):
    def __init__(self, hidden_size, n_layers, n_heads, vocab_size=50000):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, hidden_size)
        self.blocks = nn.Sequential(*[
            TransformerBlock(hidden_size, n_heads) for _ in range(n_layers)
        ])
        self.lm_head = nn.Linear(hidden_size, vocab_size)

    def forward(self, x):
        x = self.embed(x)
        x = self.blocks(x)
        return self.lm_head(x)

# === Estimate Params ===
def estimate_params(n_layers, hidden_size, vocab_size):
    return (vocab_size * hidden_size +
            n_layers * (12 * hidden_size**2) +
            hidden_size * vocab_size)

def find_divisible_heads(hidden, max_heads=32):
    for h in reversed(range(1, max_heads + 1)):
        if hidden % h == 0:
            return h
    return 1  # fallback, extremely rare

def score_benchmark(params: int, time_taken: float) -> int:
    if time_taken >= 60:
        print("[FAIL] Time exceeded 60 seconds — too slow to train anything practical.")
        return 0

    params_m = params / 1_000_000
    if time_taken < 1:
        multiplier = 2.0
    elif time_taken < 5:
        multiplier = 1.75
    elif time_taken < 10:
        multiplier = 1.3
    elif time_taken < 30:
        multiplier = 1.0
    else:
        multiplier = 0.5

    return round(params_m * multiplier)

# === Benchmark ===
def run_benchmark(device):
    hidden = 256
    layers = 4
    vocab_size = 50000
    batch_size = 2
    context_len = 512
    step = 25
    timeout = 60
    score = 0
    best_params = 0

    print(f"LM Bench, Verson 1.0, Device stress test with LLM training sim")
    print(f"Starting benchmark on device: {device}\n")

    while True:
        try:
            n_heads = find_divisible_heads(hidden)
            model = TestModel(hidden, layers, n_heads, vocab_size).to(device)
            model.train()
            opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

            x = torch.randint(0, vocab_size, (batch_size, context_len)).to(device)
            y = torch.randint(0, vocab_size, (batch_size, context_len)).to(device)

            start_time = time.time()
            out = model(x)
            loss = nn.CrossEntropyLoss()(out.view(-1, vocab_size), y.view(-1))
            loss.backward()
            opt.step()
            duration = time.time() - start_time

            param_est = estimate_params(layers, hidden, vocab_size)
            model_size_m = param_est // 1_000_000
            score = score_benchmark(param_est, duration)
            best_params = max(best_params, param_est)

            status_line = f"LM Bench | {model_size_m}M | {duration:.2f}s | Score: {score}       "
            sys.stdout.write("\r" + status_line)
            sys.stdout.flush()

            if duration > timeout:
                print(f"\nTimeout hit ({duration:.2f}s > {timeout}s)")
                break

            hidden += step
            layers += 1

            del model, x, y, out, loss, opt
            if device.type == "cuda":
                torch.cuda.empty_cache()
            elif device.type == "mps":
                try:
                    torch.mps.empty_cache()
                except:
                    pass

        except RuntimeError as e:
            print(f"\nRuntimeError: {str(e)}")
            break

    print(f"\nFinal Score: {score}")
    print(f"Largest model trained: {best_params / 1_000_000:.2f}M parameters")

def main():
    args = parse_args()
    try:
        device = get_device(args.device)
        run_benchmark(device)
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
