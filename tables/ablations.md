| Variant | Labels | Status | Trainable params | AUC_in | AUC_out | Δ vs LoRA (in) | Δ vs LoRA (out) | Δ vs PFT (in) | Δ vs PFT (out) |
|---|---|---|---|---|---|---|---|---|---|
| lora_last2 | 1% | complete | 38,402 | 0.752 ± 0.106 | 0.530 ± 0.042 | +0.012 [-0.038, 0.064] no_detectable_difference | -0.071 [-0.115, -0.028] no_detectable_difference | -0.018 [-0.060, 0.021] no_detectable_difference | -0.020 [-0.060, 0.021] no_detectable_difference |
| lora_last2 | 10% | complete | 38,402 | 0.846 ± 0.078 | 0.521 ± 0.058 | -0.053 [-0.101, -0.012] no_detectable_difference | -0.188 [-0.248, -0.129] b_better | +0.021 [-0.034, 0.072] no_detectable_difference | -0.061 [-0.109, -0.011] b_better |
| lora_last2 | 100% | complete | 38,402 | 0.942 ± 0.008 | 0.763 ± 0.016 | -0.016 [-0.041, 0.003] no_detectable_difference | -0.042 [-0.079, -0.007] b_better | -0.002 [-0.031, 0.024] no_detectable_difference | -0.000 [-0.035, 0.036] no_detectable_difference |
| lora_rank4 | 10% | complete | 112,130 | 0.818 ± 0.153 | 0.512 ± 0.055 | -0.081 [-0.139, -0.021] no_detectable_difference | -0.197 [-0.260, -0.131] b_better | nan | nan |
| lora_rank16 | 10% | complete | 443,906 | 0.801 ± 0.127 | 0.506 ± 0.114 | -0.098 [-0.158, -0.036] no_detectable_difference | -0.204 [-0.257, -0.153] b_better | nan | nan |
| pft_depth4 | 10% | complete | 7,103,234 | 0.747 ± 0.051 | 0.607 ± 0.048 | nan | nan | -0.078 [-0.151, 0.002] no_detectable_difference | +0.025 [-0.028, 0.078] no_detectable_difference |
| lora_no_augmentation | 10% | complete | 222,722 | 0.845 ± 0.069 | 0.629 ± 0.121 | -0.054 [-0.100, -0.008] no_detectable_difference | -0.080 [-0.119, -0.045] no_detectable_difference | nan | nan |
