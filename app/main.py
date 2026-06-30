def main():
    print("Welcome to AI Career Coach")
    print("-" * 27)

    cv_path = input("Please enter your CV PDF path: ")
    target_role = input("Which role are you targeting? ")

    print("\nSummary:")
    print(f"CV Path: {cv_path}")
    print(f"Target Role: {target_role}")


if __name__ == "__main__":
    main()