from statistics import fmean

VALID_METRICS = {"makespan", "power", "energy", "carbon", "cost"}
TAU = 0.05


def compute_scan_size_ratio(smri_sizes, fmri_sizes):
    smri, fmri = list(smri_sizes), list(fmri_sizes)
    if not smri:
        return 0.0
    if not fmri or fmean(fmri) == 0:
        return float("inf")
    return fmean(smri) / fmean(fmri)


def select_cluster_configuration(M, R, tau=TAU):
    if M not in VALID_METRICS:
        raise ValueError(f"Unknown metric {M!r}; expected one of {sorted(VALID_METRICS)}.")
    if M == "makespan":
        return "C2" if R >= tau else "C1"
    if M in {"power", "energy", "carbon"}:
        return "C2"
    return "C3"


if __name__ == "__main__":
    for M in VALID_METRICS:
        print(M, select_cluster_configuration(M, R=0.036))
