"""CLI for classifying one Person 1 candidate packet."""

import argparse
import json
import os
import sys

from src.classifier import CandidateClassifier, CandidateError, create_ollama_classifier
from src.client import BackendError, post_incident


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_json", help="Path to a candidate packet JSON file")
    parser.add_argument("--runtime", choices=("stub", "ollama"), default=os.getenv("VLM_RUNTIME", "stub"))
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "moondream"))
    parser.add_argument("--ollama-url", default=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("VLM_TIMEOUT_SECONDS", "60")))
    parser.add_argument("--max-image-bytes", type=int,
                        default=int(os.getenv("VLM_MAX_TOTAL_IMAGE_BYTES", str(16 * 1024 * 1024))))
    parser.add_argument("--post", action="store_true", help="POST the result to Person 3's /api/incidents")
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000"))
    args = parser.parse_args()
    try:
        with open(args.candidate_json, encoding="utf-8") as handle:
            candidate = json.load(handle)
        classifier = (create_ollama_classifier(base_url=args.ollama_url, model=args.model,
                                                timeout_seconds=args.timeout,
                                                max_total_image_bytes=args.max_image_bytes)
                      if args.runtime == "ollama" else CandidateClassifier())
        incident = classifier.classify_candidate(candidate)
        print(json.dumps(incident, indent=2))
        if args.post:
            try:
                post_incident(incident, base_url=args.backend_url)
            except BackendError as exc:
                print(f"backend error: {exc}", file=sys.stderr)
                return 3
        return 0 if incident["status"] != "failed" else 1
    except (CandidateError, OSError, json.JSONDecodeError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
