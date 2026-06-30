from pdf_reader import extract_text


def main():
    print("Welcome to AI Career Coach")
    print("-" * 27)

    cv_path = input("Please enter your CV PDF path: ")

    try:
        cv_text = extract_text(cv_path)

        print("\nPDF successfully read!")
        print("-" * 27)
        # Temporary output for development testing
        print(cv_text[:1000])  # # First 1000 characters

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()