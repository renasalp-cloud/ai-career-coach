from app.pdf_reader import extract_text
from app.ai.analyzer import analyze_cv


def main():
    print("Welcome to AI Career Coach")
    print("-" * 27)

    cv_path = input("Please enter your CV PDF path: ")
    target_role = input("Target role: ")

    try:
        cv_text = extract_text(cv_path)

        print("\nAnalyzing CV...\n")

        analysis = analyze_cv(cv_text, target_role)

        print("=" * 60)
        print(analysis)
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()