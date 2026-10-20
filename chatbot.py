"""
CogniStudy Pro™ — Interactive CLI Assistant.
Terminal-based interactive RAG query interface with persona switching.
"""

import sys
from dotenv import load_dotenv

# Safe UTF-8 console output for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.rag.engine import CogniStudyRAGEngine
from app.models.schemas import QueryRequest, StudyMode

load_dotenv()


def main():
    print("=" * 65)
    print("  [CogniStudy Pro] Interactive Terminal Assistant")
    print("=" * 65)
    print("Commands:")
    print("  :mode <student|executive|researcher|exam_cram>  - Switch persona")
    print("  :modes                                         - List all personas")
    print("  :docs                                          - List indexed documents")
    print("  exit / quit                                    - Exit assistant\n")

    engine = CogniStudyRAGEngine()
    current_mode = StudyMode.STUDENT
    user_id = "cli_user"

    # Check if any documents exist; if not, check default index
    docs = engine.get_user_documents(user_id)
    if not docs:
        print("[i] Connected to knowledge base. You can start asking questions!\n")

    while True:
        try:
            prompt_label = f"[{current_mode.value.upper()}] Ask Question"
            question = input(f"{prompt_label} > ").strip()

            if not question:
                continue

            if question.lower() in ("exit", "quit", ":q"):
                print("Goodbye!")
                break

            if question.startswith(":mode "):
                mode_str = question.split()[1].lower()
                try:
                    current_mode = StudyMode(mode_str)
                    print(f"[OK] Persona switched to: {current_mode.value.upper()}\n")
                except ValueError:
                    print("[!] Invalid mode. Choose from: student, executive, researcher, exam_cram\n")
                continue

            if question == ":modes":
                print("\nAvailable Study Modes:")
                print("  * student: Socratic breakdown, analogies, step-by-step logic")
                print("  * executive: High-level TL;DR, key findings, strategic next steps")
                print("  * researcher: Academic precision, exact citations, empirical data")
                print("  * exam_cram: High-yield revision points, mnemonics, active recall\n")
                continue

            if question == ":docs":
                user_docs = engine.get_user_documents(user_id)
                print(f"\nIndexed Documents ({len(user_docs)}):")
                for d in user_docs:
                    print(f"  * {d.get('filename')} ({d.get('chunk_count')} chunks)")
                print()
                continue

            # Execute Query
            req = QueryRequest(
                user_id=user_id,
                question=question,
                mode=current_mode,
                top_k=4
            )
            response = engine.query(req)

            print("\n" + "-" * 55)
            print(response.answer)
            print("-" * 55)

            if response.citations:
                print("[Sources]:")
                for c in response.citations:
                    page_info = f" (Page {c.page_number})" if c.page_number else ""
                    print(f"  * {c.source_file}{page_info}")
            print(f"Latency: {response.response_time_ms}ms | Retrieved Chunks: {response.chunks_retrieved}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n[!] Error: {e}\n")


if __name__ == "__main__":
    main()