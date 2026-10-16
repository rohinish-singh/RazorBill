"""Print a deterministic, schema-shaped classification for a candidate JSON file."""

import argparse
import json

from src.classifier import CandidateClassifier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_json", help="Path to a candidate packet JSON file")
    args = parser.parse_args()
    with open(args.candidate_json, encoding="utf-8") as handle:
        candidate = json.load(handle)
    print(json.dumps(CandidateClassifier().classify_candidate(candidate), indent=2))


if __name__ == "__main__":
    main()
